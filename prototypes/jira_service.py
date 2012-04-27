"""
Prototype JIRA reading service. 

Hits JIRA every 60 seconds and stores the issues it sees in a local data store,
currently sqlite3-based.
"""
from twisted.enterprise import adbapi
from twisted.web.xmlrpc import Proxy
from twisted.internet import task
from twisted.internet import reactor
import json, urllib, sys, shelve
from getpass import getpass

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
        
        # 'c' means create the db file if it doesn't exist
        self.db = shelve.open(self.db_file, 'c')
        
        self.proxy = Proxy('https://%s/jira/rpc/xmlrpc' % (self.host), self.username, self.password, allowNone=True)
        
        # log in, stash the auth token
        d = self.proxy.callRemote('jira1.login', self.username, self.password)
        d.addCallback(self.set_auth_token)
    
    def set_auth_token(self, token):
        """
        Callback to set the auth token after logging in, for future use
        """
        self.auth = token
    
    def update_db(self, issues):
        import ipdb; ipdb.set_trace()
        
    def jira_error(self):
        print >>sys.stdout, "ERROR"
        sys.stdout.flush()
        
    def __call__(self):
        d = self.proxy.callRemote('jira1.getIssuesFromFilter', self.auth, self.filter_id)
        d.addCallback(self.update_db)
        d.addErrback(self.jira_error)
        

settings = json.load(file('settings.json', 'rb'))

if not settings['password']:
    settings['password'] = getpass("Please enter your JIRA password: ")

l = task.LoopingCall(JIRAConsumer(**settings))
l.start(settings['interval'])

reactor.run()

