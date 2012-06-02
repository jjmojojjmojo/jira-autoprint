"""
Test the interfaces
"""

from unittest import TestCase

class TestRendererInterface(TestCase):
    """
    Vet the approach of the IRenderer interface 
    """
    
    def _interface(self):
        """
        Build an interface class based on IRenderer
        """
        from autoprint.interfaces import IRenderer
        from zope.schema import Choice, Int, Bool, Text
        import re
        
        class IBusinessCardRenderer(IRenderer):
            """
            Renders a standard Business Card
            """
            text_color = Choice(
                values=[u'black', u'blue', u'green'], 
                default=u'blue',
            )
            
            name = Text(
                title=u"First/Last Name",
                required=True,
            )
            
            phone = Text(
                title=u"Phone #",
                required=True,
                constraint=re.compile("\(\d\d\d\) \d\d\d-\d\d\d\d").match
            )
        
        return IBusinessCardRenderer
        
    def _renderer(self):
        """
        Create a dummy renderer
        """
        from zope.interface import implements
        
        class BusinessCardRenderer():
            implements(self._interface())
            
            title = "Business Card"
            
            def __call__(self, data):
                return "/tmp/dummy_output.pdf"
                
    def _service(self):
        """
        Create a dummy service
        """
        from zope.interface import implements
        
