"""
Rewrite of the print service as a RESTful API using twisted.web
"""

from twisted.web.server import Site, NOT_DONE_YET
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
import cups, pprint, os
from .renderers import IRenderer

from zope.component import getFactoriesFor, createObject

from jinja2 import Environment, FileSystemLoader

templates = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class JinjaTemplateResource(Resource):
    """
    Add jinja2 template processing functionality
    """
    template = None # a Jinja2 template object - instantiate when building the class
    
    def _render_template(self, data, request):
        """
        Callback to render the primary template from a deferred.
        """
        request.write(self.template.render(data).encode('utf-8'))
        request.finish()
        
    def render_template(self, data, request):
        """
        Render the primary template, deferred to a thread
        """
        d = deferToThread(self._render_template, data, request)
        return NOT_DONE_YET

class PrintDocument(JinjaTemplateResource):
    """
    GET - return a form where the user can punch in some values for the 
          renderer
          
    POST - return the rendered PDF
    PUT - send the PDF to the printer
    """
    
    template = templates.get_template('print.jinja2')
    
    def render_GET(self, request):
        data = {
            'request': request,
            'renderers': request.transport.protocol.factory.renderers
        }
        
        self.render_template(data, request)
        
        return NOT_DONE_YET

        
    def render_POST(self, request):
        data = {
            'request': request,
        }
        
        self.render_template(data, request)
        
        return NOT_DONE_YET
        
    def render_PUT(self, request):
        return "putted"
    
class PrinterStatus(JinjaTemplateResource):
    """
    GET - display the current status of the CUPS print queue.
    """
    isLeaf = True
    
    template = templates.get_template('status.jinja2')
    
    def render_GET(self, request):
        d = request.transport.protocol.factory.CUPSPrinterStatus()
        
        def _finish_status(info):
            data = {
                'request': request,
                'attributes': pprint.pformat(info['attributes']),
                'printer': info['printer'],
            }
            
            self.render_template(data, request)
        
        d.addCallback(_finish_status)
        return NOT_DONE_YET

class PrintService(Site):
    def __init__(self, **kwargs):
        root = Resource()
        root.putChild('status', PrinterStatus())
        root.putChild('', PrintDocument())
        
        Site.__init__(self, root, **kwargs)
        
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
        
    def CUPSPrinterStatus(self):
        return deferToThread(self._printerStatus)
        
    def loadRenderers(self):
        """
        Return a list of renderer objects
        """
        factories = getFactoriesFor(IRenderer)
        
        renderers = {}
        
        for renderer, factory in factories:
            renderers[renderer] = createObject(renderer)
            
        return renderers
        
