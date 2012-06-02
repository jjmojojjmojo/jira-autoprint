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
from twisted.internet.threads import deferToThread
import cups, os, pprint

port = 1097

class CUPSPrinterRequest(Request):
    """
    Do something during a request.
    
    Also, hack out whatever we can that isn't needed.
    
    @TODO: would it be a good idea to just build a raw, not-request-aware HTTP protocol?
    """
    def server_status_error(self, info):
        """
        Handle an error condition on the status page
        """
        self.write("<h1>Printer Service Status</h1>")
        self.write("ERROR" % info)
        self.finish()
        
    def server_status_success(self, info):
        """
        Return a nice HTML page showing some useful info
        about the current printer, jobs in the queue, etc
        """
        self.write("<h1>Printer Service Status</h1>")
        self.write("<dl><dt>Default Printer</dt><dd>%(printer)s</dd>" % info)
        self.write("<h2>Additional Info</h2><pre>%s</pre>" % (pprint.pformat(info['attributes'])))
        self.finish()
    
    def server_status(self):
        d = self.transport.protocol.factory.CUPSServerStatus()
        
        d.addCallback(self.server_status_success)
        d.addErrback(self.server_status_error)
    
    def print_document(self):
        """
        Actually send a PDF to the printer
        """
        self.write("<h1>TODO</h1>")
        import ipdb; ipdb.set_trace();
        self.finish()
    
    def process(self):
        # import ipdb; ipdb.set_trace();
        
        if self.method == 'GET':
            self.server_status()
            return NOT_DONE_YET
        else:
            self.print_document()
            return NOT_DONE_YET

class CUPSPrinterProtocol(HTTPChannel):
    requestFactory = CUPSPrinterRequest
        

class CUPSPrinterFactory(HTTPFactory):
    protocol = CUPSPrinterProtocol
    
    def __init__(self, *args, **kwargs):
        """
        @TODO: what happens if the connection is closed? 
               (I don't believe cups.Connection is holding open a persistent
               connection, but this will need to be verified)
        """
        HTTPFactory.__init__(self, *args, **kwargs)
        
        self._connection = cups.Connection()
        
        # self._printFile('card.pdf')
    
    def _getStatus(self):
        """
        Do a bunch of blocking calls to get info about the CUPS server - this 
        should be wrapped by CUPSServerStatus
        """
        printer = self._connection.getDefault()
        attributes = self._connection.getPrinterAttributes(printer)
        
        return {
            'printer': printer,
            'attributes': attributes,
        }
        
    
    def _printFile(self, filename):
        """
        Send a file to CUPS, wait for the status to change, and return 
        the status.
        
        @NOTE: this is a blocking call, please use .printFile, which wraps this call
               in a deferred, and setup a callback for when it's done.
        """
        info = self._getStatus()
        import ipdb; ipdb.set_trace()
        job = self._connection.printFile(info['printer'], filename, "Auto Print Service", {})
        
        
        
    
    def CUPSServerStatus(self):
        """
        Get info about the current CUPS server.
        """
        d = deferToThread(self._getStatus)
        
        return d

    
reactor.listenTCP(port, CUPSPrinterFactory())
reactor.run()
