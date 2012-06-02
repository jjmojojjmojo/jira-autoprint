from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont

def telemetry(font, size):
    """
    Return telemetry information about a given font.
    
    Returns a dict, with the following members:
    { 
      'm_width': float, approximated 'em square' size (rough),
      'ascent': float, maximum height of text above baseline,
      'descent': float, maxmim height of text below baseline,
      'max_height': float, ascent+descent
    }
    """
    face = getFont(font).face
    
    # +30% 'fudge' factor
    m_width = stringWidth('M', font, size)*1.3
    
    ascent = float(face.ascent)*m_width/1000       
    descent = float(face.descent*-1)*m_width/1000
    
    return {
        'm_width': m_width,
        'ascent': ascent,
        'descent': descent,
        'max_height': ascent+descent,
    }

def print_centered_text(canvas, text, page_width, page_height, font, size):
    """
    Draw some text centered on the page
    """
    string_width = stringWidth(text, font, size)
    
    info = telemetry(font, size)
    
    x = (page_width/2)-(string_width/2)
    y = (page_height/2)-(info['max_height']/2)
    
    canvas.drawString(x,y,text)

class PullBox(Flowable):
    """
    A numbered checkbox with a line next to it. Size is relative to the
    width/height provided.
    
    Align can be "right" or "left" - place the box on the right or the left of the line
    
    We're doing kanban - we want to track how many times a story/task is 'pulled'
    from 'in progress', either due to an impediment or getting interrupted by 
    another item.
    
    We'll do this with a table layout, so it looks like this:
    +-------------------------------+-------------------------------+
    | +-----+                       | +-----+                       |
    | |  1  |                       | |  1  |                       |
    | +-----+   ------------------  | +-----+   ------------------  |
    | +-----+                       | +-----+                       |
    | |  2  |                       | |  2  |                       |
    | +-----+   ------------------  | +-----+   ------------------  |
    | +-----+                       | +-----+                       |
    | |  3  |                       | |  3  |                       |
    | +-----+   ------------------  | +-----+   ------------------  |
    +-------------------------------+-------------------------------+
    """
    def __init__(self, width, height, number=None, font=None, size=None, align="left"):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.number = number
        
        if not font:
            font = "Helvetica"
            
        if not size:
            size = 8
        
        self.size = size
        self.font = font
        self.align = align

    def __repr__(self):
        return "PullBox(%s)" % (self.number)

    def draw(self):
        # figure out how big the line, spacing, and box are, relative to the
        # width/height
        box_width = self.height
        spacing = self.width*0.05
        line_width = self.width-spacing-box_width
        
        box_start = 0
        line_start = box_width+spacing
        line_end = self.width
        
        if self.align == 'right':
            box_start = self.width-box_width
            line_start = 0
            line_end = line_width
        
        self.canv.setLineWidth(0.5)
        self.canv.rect(box_start, 0, box_width, box_width)
        self.canv.line(line_start, 0, line_end, 0)
        
        # center the text inside of the box
        # numbers don't typically go below baseline, so we'll just use the 
        # ascent to figure out where middle is
        if self.number:
            self.number = str(self.number)
            # +30% 'fudge' factor
            m_width = stringWidth('M', self.font, self.size)
            number_height = float(getFont(self.font).face.ascent)*m_width/1000
            number_width = stringWidth(self.number, self.font, self.size)
            
            x = box_start+(box_width/2)-(number_width/2)
            y = (box_width/2)-(number_height/2)
            
            self.canv.setFont(self.font, self.size)
            self.canv.setFillColor(lightgrey)
            self.canv.drawString(x, y, self.number)
