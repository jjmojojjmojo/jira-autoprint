"""
The Print Service
"""

from autoprint.interfaces import IPrintService
from zope.interface import implements
from twisted.application import internet, service
import pycups

class PrintServiceProtocol

class PrintService(service.Service):
    """
    Twisted service that provides a simplified RESTful API to turn structured
    requests into physical paper via CUPS
    """
    implements(IPrintService)
    
    def listRenderers(self):
        pass
        
    def lookupRenderer(self, renderer):
        pass
        
    def validateRenderer(self, renderer, data):
        return True
        
    def render(renderer, data):
        renderer_obj = self.lookupRenderer(renderer)
        
        self.validateRenderer(renderer, data)
