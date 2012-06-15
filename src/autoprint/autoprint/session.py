"""
Session interfaces and implementations.
"""
from zope.interface import Interface, Attribute, implements
from twisted.python.components import registerAdapter
from twisted.web.server import Session

class IPrintedFiles(Interface):
    """
    Mapping of all files printed with a unique id for secure-ish retrieval
    """
    
class PrintedFiles(dict):
    implements(IPrintedFiles)
    
    def __init__(self, session, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
    
registerAdapter(PrintedFiles, Session, IPrintedFiles)
