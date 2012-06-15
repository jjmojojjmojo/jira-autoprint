"""
The User Interface Service
"""

from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
from .resources import ui 

class UIService(Site):
    """
    Twisted service that delivers a 100% HTML+JS front-end 
    to the RESTFul API.
    """
    
    settings = None
    
    def __init__(self, *args, **kwargs):
        root = Resource()
        root.putChild('', ui.Main())
        root.putChild('static', ui.StaticFiles)
        
        self.settings = {}
        self.settings['print_service_port'] = kwargs.get('print_service_port', None)
        if self.settings['print_service_port']:
            del kwargs['print_service_port']
            
        self.settings['print_service_uri'] = kwargs.get('print_service_uri', None)
        if self.settings['print_service_uri']:
            del kwargs['print_service_uri']
        
        Site.__init__(self, root, **kwargs)
