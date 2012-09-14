"""
The User Interface Service
"""

from twisted.web.server import NOT_DONE_YET
from . import ConfigurableSite
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
from ..resources import ui 

class UIService(ConfigurableSite):
    """
    Twisted service that delivers a 100% HTML+JS front-end 
    to the RESTFul API.
    """
    
    _defaults = {
        'print_service_port': None,
        'print_service_uri': None,
    }
    
    def root(self):
        root = Resource()
        root.putChild('', ui.Main())
        root.putChild('static', ui.StaticFiles)
        return root
