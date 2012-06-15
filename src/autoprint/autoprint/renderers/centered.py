"""
Renderers

:todo: validation, error handling, cleanup of temporary files
"""
from zope.interface import Interface, implements, Attribute
import zope.schema, zope.component
from zope.schema.vocabulary import SimpleVocabulary
from zope.component.factory import Factory, IFactory
import tempfile

from reportlab.pdfgen import canvas
import reportlab.lib.colors
from reportlab.lib.units import inch
import reportlab.lib.pagesizes

from . import IRenderer
from .util import print_centered_text

### TODO: switch to vocabularies that are defined by the 

AVAILABLE_COLORS = {
    'Black':      reportlab.lib.colors.black,
    'Pink':       reportlab.lib.colors.pink, 
    'Red':        reportlab.lib.colors.red, 
    'Blue':       reportlab.lib.colors.blue,
    'Green':      reportlab.lib.colors.green,
    'Light Grey': reportlab.lib.colors.lightgrey,
    'Dark Grey':  reportlab.lib.colors.darkgrey, 
}

PAGE_SIZES = {
    'U.S. Letter': reportlab.lib.pagesizes.letter,
    'U.S. Legal': reportlab.lib.pagesizes.legal,
    'A4': reportlab.lib.pagesizes.A4,
}

class ICenteredPageRenderer(IRenderer):
    """
    Prints a message in the exact center of a page, defaults to 0.5" margins
    
    :todo: support custom page sizes.
    """
    message = zope.schema.Text(
        title=u"Message",
        description=u"Text to print in the center of the page",
        default=u"",
    )
    
    font = zope.schema.Choice(
        values=(u'Times', u'Courier', u'Helvetica', u'Symbol', u'Zapf Dingbats'),
        title=u"Font",
        description=u"What font to use to render the text",
        default=u'Helvetica',
    )
    
    fontsize = zope.schema.Float(
        title=u"Font Size",
        description=u"The font size to render the text in.",
        default=24.0,
    )
    
    color = zope.schema.Choice(
        title=u"Text Color",
        description=u"What color should the text be?",
        values=AVAILABLE_COLORS.keys(),
        default='Black',
    )
    
    pagesize = zope.schema.Choice(
        title=u"Page Size",
        description=u"Select a size for the page to print on",
        values=PAGE_SIZES.keys(),
        default='U.S. Letter',
    )
    
    margin = zope.schema.Tuple(
        title=u"Margins (in inches)",
        description=u"Margins: left, bottom, right, top.",
        value_type=zope.schema.Float(required=True),
        default=(0.5, 1.0, 0.5, 1.0),
        min_length = 4,
        max_length = 4,
    )

class CenteredPageRenderer:
    implements(ICenteredPageRenderer)
    
    title = "Message Centered On a Page."
    
    def __init__(self):
        junk, self.output = tempfile.mkstemp(suffix=".pdf")
    
    def __call__(self, data):
        margin_left, margin_bottom, margin_right, margin_top = data['margins']
    
        # incorporate margins
        page_width, page_height = PAGE_SIZES.get(data['pagesize'], reportlab.lib.pagesizes.letter)
        
        c = canvas.Canvas(self.output, pagesize=data['pagesize'])
        
        # 1/4" grid to check positioning
        c.setStrokeColor(reportlab.lib.colors.lightgrey)
        
        frame_width = page_width-(margin_left+margin_right)
        frame_height = page_height-(margin_top+margin_bottom)
        
        c.rect(margin_left, margin_bottom, frame_width, frame_height)
        
        # TODO: add font color
        c.setFont(data['font'], data['fontsize'])
        print_centered_text(c, data['message'], page_width, page_height, data['font'], data['fontsize'])
        
        c.showPage()
        c.save()
        
        return self.output
        
    


# register the factories in the component architecture.
factory = Factory(CenteredPageRenderer, 'Centerd Page Renderer', CenteredPageRenderer.__doc__)

zope.component.provideUtility(factory, IFactory, 'centeredpagerenderer')
