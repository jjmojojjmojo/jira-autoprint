"""
Prototype JIRA reading service. 

Hits JIRA every 60 seconds and stores the issues it sees in a local data store,
currently using shelve.

@TODO: what happens if JIRA is really slow and the call to JIRAConsumer happens while a previous call is still running?

"""
from twisted.enterprise import adbapi
from twisted.web.xmlrpc import Proxy
from twisted.internet import task
from twisted.internet import reactor
import json, urllib, sys, shelve, pprint
from getpass import getpass
from cardlayout import add_card
from StringIO import StringIO
from pyPdf import PdfFileWriter, PdfFileReader
from reportlab.lib.units import inch 
from reportlab.pdfgen.canvas import Canvas 
from datetime import datetime
from twisted.internet.threads import deferToThread
from twisted.internet import defer

class JIRAConsumer(object):
    """
    Callable that will get a list of issues from JIRA (via a filter), and stash them
    in a database.
    
    Registers a callback to do something when a new or changed issue is identified.
    """
    host = None         # JIRA host
    username = None     # JIRA username
    password = None     # JIRA password
    proxy = None        # object used for XMLRPC communication to JIRA
    auth = None         # JIRA XMLRPC authentication token
    db_file = None      # dbm file used by shelve to store 'seen' issues
    db = None           # the shelve object itself (works just like a dict)
    trigger_keys = None # keys to use to indicate that a jira issue has changed
    types = {}          # issue types, indexed by id
    priorities = {}     # issue priorities, indexed by id
    users = {}          # user info, indexed by id - loaded periodically as new users are seen
    
    def __init__(self, **kwargs):
        """
        @todo: how to prevent __call__ from being called before the login
               call returns?
        """
        self.host = kwargs['host']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.filter_id = kwargs['filter_id']
        
        self.db_file = kwargs.get('db_file', 'jira_cache.db')
        self.trigger_keys = kwargs.get('trigger_keys', ('summary', 'priority', 'type', 'description'))
        
        # 'c' means create the db file if it doesn't exist
        self.db = shelve.open(self.db_file, 'c')
        
        self.proxy = Proxy('https://%s/jira/rpc/xmlrpc' % (self.host), self.username, self.password, allowNone=True)
        
        # log in, stash the auth token
        d = self.proxy.callRemote('jira1.login', self.username, self.password)
        d.pause()
        d.addCallback(self.set_auth_token)
        d.addCallback(self.load_lookups)
        d.unpause()
    
    def process_issue_types(self, issue_types):
        types = {}
        for issue_type in issue_types:
            types[issue_type['id']] = issue_type['name']
            
        self.types = types
    
    def process_priorities(self, issue_priorities):
        priorities = {}
        for issue_priority in issue_priorities:
            priorities[issue_priority['id']] = issue_priority['name']
            
        self.priorities = priorities
    
    def load_lookups(self, auth):
        """
        Load and process lookup tables:
            issue types
            priorities
        """
        d = self.proxy.callRemote('jira1.getIssueTypes', self.auth)
        d.addCallback(self.process_issue_types)
        d = self.proxy.callRemote('jira1.getPriorities', self.auth)
        d.addCallback(self.process_priorities)
        
    
    def set_auth_token(self, token):
        """
        Callback to set the auth token after logging in, for future use
        """
        self.auth = token
    
    def update_db(self, issues):
        """
        Callback to update the shelve database with a list of changed issues
        """
        print >>sys.stdout, "Updating db with %s issues" % (len(issues))
        sys.stdout.flush()
        for issue in issues:
            self.db[issue['key']] = issue
            
        return issues
    
    def process(self, issues):
        """
        Callback to update the shelve database, and trigger our card generation
        but only if the issue has changed in areas we care about:
        
          - summary
          - issue type
          - description
          - priority
        
        @TODO: only store a subset of the data returned by the xmlrpc call?
        
        @return: Deferred with a callback registered to update_db
        """ 
        print >>sys.stdout, "Processing %s cards" % (len(issues))
        changed = []
        for issue in issues:
            existing = self.db.get(issue['key'], None)
            if not existing:
                changed.append(issue)
                continue
            else:
                # using get here in case the issues loose the 
                # parameters
                # @TODO: verify that this is necessary
                # @TODO: make the keys we care about configurable
                #
                # @NOTE: dictionary comprehensions are a python 2.7 thing
                subject = {k:v for k,v in existing.viewitems() if k in self.trigger_keys}
                comp = {k:v for k,v in issue.viewitems() if k in self.trigger_keys}
                
                if subject != comp:
                    changed.append(issue)
        
        print >>sys.stdout, "%s cards changed" % (len(changed))
        sys.stdout.flush()
        
        d = deferToThread(self.update_db, changed)
        return d
    
    def update_user(self, user):
        print >>sys.stdout, "Updating user %s " % (user['name'])
        sys.stdout.flush()
        self.users[user['name']] = user
    
    def fetch_user(self, issue):
        print >>sys.stdout, "Fetching user %s " % (issue['reporter'])
        sys.stdout.flush()
        
        user = self.users.get(issue['reporter'], None)
        
        if not user:
            d = self.proxy.callRemote('jira1.getUser', self.auth, issue['reporter'])
            d.addCallback(self.update_user)
            return d
    
    def update_users(self, issues):
        """
        Update the internal cache of user info for a set of new issue cards, 
        calling out to JIRA for anyone we haven't seen before
        
        @TODO: handle this more efficiently!
        @TODO: what happens when a user is updated. This method would mean they are
               out of date until the service is restarted.
        """
        print >>sys.stdout, "Updating users for %s cards" % (len(issues))
        sys.stdout.flush()
        user_deferreds = []
        
        for issue in issues:
            d = defer.maybeDeferred(self.fetch_user, issue)
            user_deferreds.append(d)
                
        dl = defer.DeferredList(user_deferreds)
        dl.addErrback(self.jira_error)
        dl.addCallback(lambda x: issues) 
        return dl
    
    def print_cards(self, issues):
        """
        Generate a PDF file with the changed issues
        
        In the final version of this service, it will send the issue data to the
        print service via REST instead of doing all of this file IO
        
        Returns the name of the file created.
        
        @TODO: this writes a file - defer it to a thread
        """
        
        if not issues:
            return
        
        print >>sys.stdout, "Printing %s cards" % (len(issues))
        
        for issue in issues:
            reporter = self.users.get(issue['reporter'], "UNKNOWN")
            print >>sys.stdout, issue['reporter']
            print >>sys.stdout, pprint.pformat(reporter)
        
        sys.stdout.flush()
        
        output_file = datetime.now().strftime("%Y%m%d-%H%M%S")+'.pdf'
        
        # 5 x 3 index card size
        page_width = 5*inch
        page_height = 3*inch
        canvas = Canvas(output_file, pagesize=(page_width, page_height))  
        
        for issue in issues:
            story_info = {
                'summary': issue['summary'],
                'detail': issue['description'],
                'id': issue['key'],
                'type': self.types.get(issue['type'], 'Unknown'),
                'reporter': self.users[issue['reporter']]['fullname'],
                'date': datetime.strptime(issue['created'], "%Y-%m-%d %H:%M:%S.0"),
                'icon': 'agt_utilities.png',
            }
            
            story_info['formatted_date'] = story_info['date'].strftime('%m/%d @ %I:%M %p')
            
            add_card(canvas, story_info, page_width, page_height);
        
        canvas.save()
        
        return output_file
        
    def jira_error(self, error):
        error.printBriefTraceback()
        # print >>sys.stdout, "ERROR"
        # sys.stdout.flush()
        
    def __call__(self):
        d = self.proxy.callRemote('jira1.getIssuesFromFilter', self.auth, self.filter_id)
        d.addErrback(self.jira_error)
        d.addCallback(self.process)
        d.addCallback(self.update_users)
        d.addCallback(self.print_cards)
        
        
        

settings = json.load(file('settings.json', 'rb'))

if not settings['password']:
    settings['password'] = getpass("Please enter your JIRA password: ")

l = task.LoopingCall(JIRAConsumer(**settings))
l.start(settings['interval'])

reactor.run()

