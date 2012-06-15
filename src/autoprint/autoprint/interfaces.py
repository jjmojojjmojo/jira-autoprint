"""
Printing Service - Interfaces

:author: Josh Johnson <lionface.lemonface@gmail.com>
"""

from zope.interface import Interface, Attribute 

class IPrintService(Interface):
    """
    Marshalls information between a remote user and an object that implements 
    :class:`IRenderer`.
    """
    
    def listRenderers():
        """
        Returns a list of all the objects that implement :class:`IRenderer`
        """
    
    def lookupRenderer(renderer):
        """
        Given a Renderer name, returns the renderer.
        """
        
    def validateRenderer(renderer, data):
        """
        Validate all of the fields in the renderer
        """
        
    def print(renderer, data):
        """
        Given an Renderer and the requisite data, sends it to the CUPS queue.
        """
    
class IRenderer(Interface):
    """
    Callable that creates a printable file (typically PDF), and returns a path 
    to that file.
    """
    title = Attribute("Brief, but descriptive title for this renderer")
    description = Attribute("More detail about what this renderer does")
    
    def validate(data):
        """
        Validate field information sent from a remote user. Raises 
        :class:`RendererValidationError` if something doesn't check out.
        """
    
    def build(data):
        """
        Build a printable file and return its path. Raises :class:`RendererBuildError`
        if anything goes wrong.
        """
    
    def __call__(data):
        """
        Given the data, return a file location of a rendered file. Implies calls 
        to :method:`validate()` and :method:`build()`.
        """
        
