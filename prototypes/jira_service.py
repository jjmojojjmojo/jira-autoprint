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

# quick and dirty way to associate my own icons with 
# jira types
icons = {
    'Operational Task': 'cards-heart.png',
    'Task': 'agt_utilities.png',
    'Story': 'agt_utilities.png',
    'Epic': 'globe2.png',
    'Improvement': 'agt_utilities.png',
    'Bug': 'tools-report-bug.png',
    'Unknown': 'agt_utilities.png',
}

priority_icons = {
    'Blocker': 'software-update-urgent-2.png',
    'Critical': 'emblem-important-3.png',
    'Major': 'emblem-special.png',
    'Minor': 'emblem-generic.png',
    'Trivial': 'emblem-generic.png',
    'Unknown': 'face-uncertain.png',
}

priority_colors = {
    'Blocker': '#F56C6C',
    'Critical':  '#F56C6C',
    'Major':  '#EEEEEE',
    'Minor': '#CEE8F0',
    'Trivial': '#CEE8F0',
    'Unknown': '#FFFFFF',
}

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
        d1 = self.proxy.callRemote('jira1.login', self.username, self.password)
        d1.pause()
        d1.addCallback(self.set_auth_token)
        d1.addCallback(self.load_lookups)
        d1.unpause()
        
    
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
        
        d1 = self.proxy.callRemote('jira1.getIssueTypes', self.auth)
        d1.addCallback(self.process_issue_types)
        d2 = self.proxy.callRemote('jira1.getPriorities', self.auth)
        d2.addCallback(self.process_priorities)
        
        return defer.DeferredList([d1, d2])
        
    
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
                print >>sys.stdout, "%s is not in the db" % (issue['key'])
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
                    print >>sys.stdout, "%s has changed" % (issue['key'])
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
        else:
            return user
    
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
        
        sys.stdout.flush()
        
        output_file = datetime.now().strftime("%Y-%m-%d-%H%M%S")+'.pdf'
        
        # 5 x 3 index card size
        page_width = 5*inch
        page_height = 3*inch
        canvas = Canvas(output_file, pagesize=(page_width, page_height))  
        
        for issue in issues:
            
            # print >>sys.stdout, pprint.pformat(issue)
            # sys.stdout.flush()
            
            issue_type = self.types.get(issue['type'], 'Unknown')
            icon = icons.get(issue_type, icons['Unknown'])
            
            issue_priority = self.priorities.get(issue['priority'], 'Unknown')
            priority_icon = priority_icons.get(issue_priority, priority_icons['Unknown'])
            priority_color = priority_colors.get(issue_priority, priority_colors['Unknown'])
            
            story_info = {
                'summary': issue['summary'],
                'detail': issue.get('description', ''),
                'id': issue['key'],
                'type': issue_type,
                'reporter': self.users[issue['reporter']]['fullname'],
                'date': datetime.strptime(issue['created'], "%Y-%m-%d %H:%M:%S.0"),
                'icon': icon,
                'priority_icon': priority_icon,
                'header_bg_color': priority_color,
            }
            
            story_info['formatted_date'] = story_info['date'].strftime('%m/%d @ %I:%M %p')
            
            add_card(canvas, story_info, page_width, page_height);
        
        canvas.save()
        
        print >>sys.stdout, "Wrote %s" % (output_file)
        sys.stdout.flush()
        
        return output_file
        
    def jira_error(self, error):
        error.printBriefTraceback()
        # print >>sys.stdout, "ERROR"
        # sys.stdout.flush()
    
    def cull_db(self):
        """
        Get rid of cached issues that are more than a week old
        
        @TODO: this could be very slow - this might be a good case for switching to sqlite.
        """
        
    def __call__(self):
        d = self.proxy.callRemote('jira1.getIssuesFromFilter', self.auth, self.filter_id)
        d.pause()
        d.addErrback(self.jira_error)
        d.addCallback(self.process)
        d.addCallback(self.update_users)
        d.addCallback(self.print_cards)
        d.unpause()
        
        
        

settings = json.load(file('settings.json', 'rb'))

if not settings['password']:
    settings['password'] = getpass("Please enter your JIRA password: ")

job = JIRAConsumer(**settings)

l = task.LoopingCall(job)
l.start(settings['interval'])

reactor.run()

