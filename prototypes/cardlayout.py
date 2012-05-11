"""
Prototype of a layout for a User Story/agile item on a 3.5x5" notecard.

Attempting to use Platypus for this purpose.
"""
import cups, os
from datetime import datetime
import reportlab.graphics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, Table, TableStyle, KeepInFrame
from reportlab.platypus.flowables import Flowable, XBox, Image
from reportlab.pdfgen.canvas import Canvas 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.lib.colors import pink, black, red, blue, green, lightgrey, darkgrey
from StringIO import StringIO
from pyPdf import PdfFileWriter, PdfFileReader
from svglib.svglib import svg2rlg

def add_card(canvas, story_info, page_width, page_height, border=False):
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = "Helvetica"
    styles['BodyText'].fontSize = 12
    
    # using a uniform margin for now
    margin = inch*0.15
    
    ######## frames for better layout control
    frame_width = page_width-(margin*2)
    frame_height = page_height-(margin*2)
    
    # the whole printable area
    main = Frame(margin, margin, frame_width, frame_height, showBoundary=0, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
    footer = Frame(margin, margin, frame_width, frame_height, showBoundary=0, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
    ###### drop in a few background elements
    #
    
    # drop in a prebuild bg from an SVG file
    # background = svg2rlg("kanban card background.svg")
    # reportlab.graphics.renderPDF.draw(background, canvas, 0, 0)
    
    # add a border around the whole page to make it easier to cut out of a full
    # sheet of paper
    if border:
        canvas.setLineWidth(0.5)
        canvas.rect(1, 1, page_width-2, page_height-2, stroke=1, fill=0)
    
    # label the checkbox arrays with a rotated text label
    canvas.saveState()
    canvas.setFillColor((0.9, 0.9, 0.9))
    canvas.setFont('Helvetica-Bold', 20)
    canvas.translate(margin*2, margin*2)
    canvas.rotate(15)
    canvas.drawString(0, -10, "INTERRUPTED")
    canvas.restoreState()
    
    canvas.saveState()
    canvas.setFillColor((0.9, 0.9, 0.9))
    canvas.setFont('Helvetica-Bold', 20)
    canvas.translate(frame_width/2+(inch*0.6), margin*2)
    canvas.rotate(15)
    canvas.drawString(0, -10, "BLOCKED")
    canvas.restoreState()
    
    ######### use a table to hold the header
    #
    # +--------+-------------------------+-------+
    # | ID     | Reporter                | Icon  |
    # | Type   | Created Date            |       |
    # +--------+-------------------------+-------+
    #
    # Illustrates the use of inline styling.
    #
    # @TODO: move the inline styles to the style sheet
    header_data = [
        [ 
          Image(story_info['icon'], inch*0.4, inch*0.4),
          [
           Paragraph('<para size="18"><b>%(id)s</b></para>' % story_info, styles['BodyText']), 
           Spacer(1,2),
           Paragraph('<para size="8">%(type)s</para>' % story_info, styles['BodyText']),
          ],
          [
           Paragraph('<para size="16" alignment="center"><u>%(reporter)s</u></para>' % story_info, styles['BodyText']),  
           Spacer(1,2),
           Paragraph('<para size="10" alignment="center"><b>Opened: %(formatted_date)s</b></para>' % story_info, styles['BodyText']), 
          ],
          # XBox(inch*0.4, inch*0.4, ""),
          Image(story_info['priority_icon'], inch*0.4, inch*0.4),
        ],
    ]
    
    # set the alignment
    header_style = TableStyle([
        ('ALIGNMENT',       (0,0),  (-1,-1),  'CENTER'), 
        ('VALIGN',          (0,0),  (-1,-1),  'MIDDLE'),
        ('LEFTPADDING',     (0,0),  (-1,-1),  3),
        ('RIGHTPADDING',    (0,0),  (-1,-1),  3),
        ('TOPPADDING',      (0,0),  (-1,-1),  3),
        ('BOTTOMPADDING',   (0,0),  (-1,-1),  3),
        ('BACKGROUND',      (0,0),  (-1,-1), story_info['header_bg_color']),
        ('BOX',             (0,0),  (-1,-1), 0.5, black),
        # exceptions for the first cell
        ('ALIGNMENT',       (0,0),  (0,0),  'LEFT'), 
    ])
    
    header = Table(header_data, colWidths=[ 0.6*inch, inch*1.2, None, 0.6*inch], style=header_style)
    
    # The text of the story
    story = Paragraph("<b>"+story_info['summary']+"</b>", styles['BodyText'])
    
    # the text of the description - just the first 20 words 
    detail_words = story_info['detail'].split()
    
    short_detail = " ".join(detail_words[:50])
    
    if len(detail_words) > 50:
        short_detail += '...'
    
    details = KeepInFrame(frame_width, frame_height/3, [Paragraph(short_detail, styles['BodyText']),], mode="shrink", mergeSpace=0)
    
    # We're doing kanban - we want to track how many times a story/task is 'pulled'
    # from 'in progress', either due to an impediment or getting interrupted by 
    # another item.
    #
    # We'll do this with a table layout, so it looks like this:
    # +-------------------------------+-------------------------------+
    # | +-----+                       | +-----+                       |
    # | |  1  |                       | |  1  |                       |
    # | +-----+   ------------------  | +-----+   ------------------  |
    # | +-----+                       | +-----+                       |
    # | |  2  |                       | |  2  |                       |
    # | +-----+   ------------------  | +-----+   ------------------  |
    # | +-----+                       | +-----+                       |
    # | |  3  |                       | |  3  |                       |
    # | +-----+   ------------------  | +-----+   ------------------  |
    # +-------------------------------+-------------------------------+
    #   
    # We'll do this with a custom flowable
    class PullBox(Flowable):
        """
        A numbered checkbox with a line next to it. Size is relative to the
        width/height provided.
        
        Align can be "right" or "left" - place the box on the right or the left of the line
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
    
    # special style to get rid of all padding
    NoPadding = TableStyle([
            ('LEFTPADDING',     (0,0),  (-1,-1),  0),
            ('RIGHTPADDING',    (0,0),  (-1,-1),  0),
            ('TOPPADDING',      (0,0),  (-1,-1),  0),
            ('BOTTOMPADDING',   (0,0),  (-1,-1),  0),
    ]) 
    
    checkbox_style = TableStyle([
            ('LEFTPADDING',     (0,0),  (-1,-1),  6),
            ('RIGHTPADDING',    (0,0),  (-1,-1),  6),
            ('TOPPADDING',      (0,0),  (-1,-1),  6),
            ('BOTTOMPADDING',   (0,0),  (-1,-1),  6),
    ])
    
    checkbox_width = (frame_width/2)-6
    
    interrupted_data = [
        [PullBox(checkbox_width, inch*0.15, 1),],
        [PullBox(checkbox_width, inch*0.15, 2),],
        [PullBox(checkbox_width, inch*0.15, 3),],
    ]
    
    interrupted_table = Table(interrupted_data)
    
    blocked_data = [
        [PullBox(checkbox_width, inch*0.15, 1, align="right"),],
        [PullBox(checkbox_width, inch*0.15, 2, align="right"),],
        [PullBox(checkbox_width, inch*0.15, 3, align="right"),],
    ]
    
    blocked_table = Table(blocked_data)
    
    checkboxes = Table(
        [[interrupted_table, blocked_table],],
        style=NoPadding,
    )
    
    main.addFromList(
        [
            header,
            story, 
            details,
        ],
        canvas
    )
    
    # use translate to get the checkboxes to always render at the bottom of the
    # page, even if the summary text is short.
    story_width, story_height  = story.wrap(frame_width, frame_height)
    checkboxes_width, checkboxes_height  = checkboxes.wrapOn(canvas, frame_width, frame_height)
    
    # 
    canvas.saveState()
    canvas.translate(0, -frame_height+checkboxes_height)
    footer.addFromList([checkboxes,], canvas)
    canvas.restoreState()
    
    canvas.showPage()


if __name__ == '__main__':
    ##############################
    # New method is to use svglib to render an SVG background behind the card
    #
    # Old method - use pypdf to render an existing PDF behind the card
    #
    # 
    output = 'card.pdf'
    
    # 5 x 3 index card size
    page_width = 5*inch
    page_height = 3*inch
    canvas = Canvas(output, pagesize=(page_width, page_height))
    
    story_info = {
        'summary': "Install Perl module TAP::Harness::JUnit on development environment",
        'detail': """
        We, the Legacy team, want to begin using Bamboo to run our unit tests when committing code.  As I understand it, Bamboo needs the tests to output results in an XML format.  In my research, the only way to do this is by using TAP::Harness::JUnit.
        
        So, please install TAP::Harness::JUnit on daisy2, my development server.  If this does work the way I think, the module will need to be installed on the server that Bamboo will use to run the unit tests.
        """,
        'id': 'CI-687',
        'type': "Operational Task",
        'reporter': 'Rob Reece',
        'date': datetime.now(),
        'icon': 'agt_utilities.png',
        'priority': 'Critical',
        'priority_icon': 'software-update-urgent-2.png',
        #'header_bg_color': (1, 0, 0),
        'header_bg_color': '#FF0000',
    }
    
    # story_info['formatted_date'] = story_info['date'].strftime('%m/%d @ %I:%M %p')
    story_info['formatted_date'] = "4/25 @ 12:23PM"
    
    add_card(canvas, story_info, page_width, page_height);
    
    canvas.save()
   
   
