"""
The Print Service
"""

from twisted.web.server import NOT_DONE_YET
from . import ConfigurableSite
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
import cups, pkg_resources
from ..resources import appstatus, renderers
from ..util import loadRenderers

class PrintService(ConfigurableSite):
    """
    Twisted service that provides a simplified RESTful API to turn structured
    requests into physical paper via CUPS
    """
    _defaults = {
        'imagemagick_path': None,
        'thumbnail_width': None,
        'printer_to_use': None,
        'working_directory': None,
    }
    
    def root(self):
        root = Resource()
        
        root.putChild("", appstatus.ServiceStatus())
        root.putChild("status", appstatus.ServiceStatusJSON())
        root.putChild("renderers", renderers.RendererAPI())
        root.putChild("history", renderers.RendererPrintedList())
        
        return root
    
    def __init__(self, **kwargs):
        ConfigurableSite.__init__(self, **kwargs)
        
        self._connection = cups.Connection()
        self.renderers = loadRenderers()
        self.printer = self._connection.getDefault()

    
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
        
    def printFile(self, path, title):
        """
        Send a file to the print queue.
        """
        
        return deferToThread(self._connection.printFile,
            title=title,           # title
            printer=self.printer,       # the printer to use (it's name)
            filename=path,         # file to print
            options={},
        )
