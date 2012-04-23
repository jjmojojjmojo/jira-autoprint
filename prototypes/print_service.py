"""
Prototype for print service

Basic process flow:
    - Service receives an HTTP POST request containing JSON data
    - Service dispatches to a 'renderer', a callable that takes the data, writes
      a PDF (or some other file that cups can print), and returns the file path
    - Service adds the path to the CUPS print queue.
    
Assumptions:
    - You trust everything that's coming in
    - You are running this service on the same machine as CUPS
    - You're OK with the default printer, using the default settings
    
"""
from twisted.web.http import HTTPFactory, HTTPChannel, Request
from twisted.protocols.basic import LineReceiver
from twisted.web.server import NOT_DONE_YET
from twisted.internet import reactor, defer
import cups, os

port = 1097

class CUPSPrinterRequest(Request):
    """
    Do something during a request.
    
    Also, hack out whatever we can that isn't needed.
    """
    
    def server_status(self):
        """
        Return a nice HTML page showing some useful info
        about the current printer, jobs in the queue, etc
        """
        info = self.transport.protocol.factory.server_status()
        self.write("<h1>Printer Service Status</h1>")
        self.write("<dl><dt>Default Printer</dt><dd>%(default)s</dd>" % info)
        self.finish()
    
    def print_document(self):
        """
        Actually send a PDF to the printer
        """
        self.write("<h1>TODO</h1>")
        self.finish()
    
    def process(self):
        # import ipdb; ipdb.set_trace();
        
        if self.method == 'GET':
            self.server_status()
        else:
            self.print_document()

class CUPSPrinterProtocol(HTTPChannel):
    requestFactory = CUPSPrinterRequest
        

class CUPSPrinterFactory(HTTPFactory):
    protocol = CUPSPrinterProtocol
    
    def __init__(self, *args, **kwargs):
        HTTPFactory.__init__(self, *args, **kwargs)
        
        self._connection = cups.Connection()
    
    def server_status(self):
        return {
            'default': self._connection.getDefault()
        }

    
reactor.listenTCP(port, CUPSPrinterFactory())
reactor.run()
