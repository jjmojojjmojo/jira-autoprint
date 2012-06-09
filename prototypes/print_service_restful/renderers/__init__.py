"""
Common renderer classes and utilities.
"""

from zope.interface import Interface, implements, Attribute

class IRenderer(Interface):
    """
    Receives structured data from the print service, renders a PDF or other
    printable file to disk, and then returns the path so it can be passed on
    to CUPS
    """
    
    title = Attribute("Brief, but descriptive title for this renderer")
    settings = Attribute("Dictionary of lookup lists and other infrequently-configured settings, that can be overridden at run-time")
    schema = Attribute("colander schema defining required inputs")
    
    def __call__(data):
        """
        Given the data, generate a printable file and return the path to it.
        """
        
        
from .centered import CenteredPageRenderer
from .issuecard import IssueCardRenderer
