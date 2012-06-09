"""
The Print Service
"""

from twisted.web.server import Site, NOT_DONE_YET
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.static import File, NoRangeStaticProducer
from util import JinjaTemplateResource
from . import templates
from twisted.internet.threads import deferToThread
import cups, json

class ServiceStatus(JinjaTemplateResource):
    """
    Display useful status information about the 
    print service
    
    Returns HTML by default.
    
    :todo: return JSON as well with a URL param
    """
    isLeaf = True
    
    template = templates.get_template('appstatus.jinja2')
    
    def service_status(self, request):
        """
        Return a dictionary of service status information.
        
        :todo: Add in other useful information
        """
        d = request.transport.protocol.factory.printerStatus()
        
        return d
    
    def render_GET(self, request):
        
        return self.render_template(data, request)
        
class ServiceStatusJSON(ServiceStatus):
    """
    Alternate ServiceStatus
    
    Returns a JSON serialized body and sets the right header for JSON content
    """
    def render_GET(self, request):
        d = self.service_status(request)
        
        def go(data):
            request.setHeader('Content-type', 'application/json')
            request.write(json.dumps(data, sort_keys=True, indent=4)
        
        d.addCallback(go)
        
        return NOT_DONE_YET

class PrintService(Site):
    """
    Twisted service that provides a simplified RESTful API to turn structured
    requests into physical paper via CUPS
    """
    
    def __init__(self, **kwargs):
        self._connection = cups.Connection()
        self.renderers = self.loadRenderers()
    
    def _printerStatus(self):
        """
        Return a dictionary containing information about the current printer
        status.
        """
        printer = self._connection.getDefault()
        attributes = self._connection.getPrinterAttributes(printer)
        
        return {
            'printer': printer,
            'attributes': attributes,
        }
    
    def printerStatus(self):
        return deferToThread(self._printerStatus)
