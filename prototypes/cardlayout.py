"""
Prototype of a layout for a User Story/agile item on a 3.5x5" notecard.

Attempting to use Platypus for this purpose.
"""
import cups, os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, Table, TableStyle
from reportlab.platypus.flowables import Flowable, XBox, Image
from reportlab.pdfgen.canvas import Canvas 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.lib.colors import pink, black, red, blue, green, lightgrey, darkgrey

output = "card.pdf"

story_info = {
    'summary': "Build a cool automatic printing system.",
    'detail': "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Maecenas consequat bibendum est, non fermentum risus tincidunt at. Etiam auctor odio sit amet massa dignissim ullamcorper. Fusce imperdiet orci sed velit dictum non tempor est lacinia. Vestibulum faucibus augue felis. Cras eget metus vitae erat luctus iaculis at fermentum dolor. Vestibulum enim eros, hendrerit eu euismod sed, tristique vel mauris. Praesent nec iaculis nibh. Sed et augue id metus gravida facilisis et eu tellus. Aenean a erat ut augue molestie cursus et in nuncanvas. Phasellus odio elit, tincidunt et pharetra commodo, accumsan a nisi. Suspendisse posuere vestibulum nibh, eu fermentum ante sodales et. Sed quis ante quam, at pharetra felis. Praesent tincidunt, velit nec molestie euismod, diam dolor tempor eros, at gravida elit sapien ornare est.",
    'id': 'CI-999',
    'type': "Operational Task",
    'reporter': 'Bob Dobbalina',
    'date': datetime.now(),
    'icon': 'agt_utilities.png',
}

story_info['formatted_date'] = story_info['date'].strftime('%m/%d @ %I:%M %p')


styles = getSampleStyleSheet()
styles['Normal'].fontName = "Helvetica"
styles['BodyText'].fontSize = 12

# 5 x 3 index card size
page_width = 5*inch
page_height = 3*inch

canvas = Canvas(output, pagesize=(page_width, page_height))

# using a uniform margin for now
margin = inch*0.15

######## frames for better layout control
frame_width = page_width-(margin*2)
frame_height = page_height-(margin*2)

# the whole printable area
main = Frame(margin, margin, frame_width, frame_height, showBoundary=0, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)

###### drop in a few background elements
#

# add a border around the whole page to make it easier to cut out of a full
# sheet of paper
canvas.setLineWidth(0.5)
canvas.rect(1, 1, page_width-2, page_height-2, stroke=1, fill=0)

# label the checkbox arrays with a rotated text label
canvas.saveState()
canvas.setFillColor((0.9, 0.9, 0.9))
canvas.setFont('Helvetica-Bold', 20)
canvas.translate(margin*2, margin*2)
canvas.rotate(25)
canvas.drawString(0, -10, "INTERRUPTED")
canvas.restoreState()

canvas.saveState()
canvas.setFillColor((0.9, 0.9, 0.9))
canvas.setFont('Helvetica-Bold', 20)
canvas.translate(frame_width/2+(inch*0.6), margin*2)
canvas.rotate(25)
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
      [
       Paragraph('<para size="18">%(id)s</para>' % story_info, styles['BodyText']), 
       Spacer(1,2),
       Paragraph('<para size="8">%(type)s</para>' % story_info, styles['BodyText']),
      ],
      [
       Paragraph('<para size="16" alignment="center"><u>%(reporter)s</u></para>' % story_info, styles['BodyText']),  
       Spacer(1,2),
       Paragraph('<para size="10" alignment="center"><b>Opened: %(formatted_date)s</b></para>' % story_info, styles['BodyText']), 
      ],
      # XBox(inch*0.4, inch*0.4, ""),
      Image(story_info['icon'], inch*0.4, inch*0.4),
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
    ('BACKGROUND',      (0,0),  (-1,-1), (0.9, 0.9, 0.9)),
    ('BOX',             (0,0),  (-1,-1), 0.5, black),
    # exceptions for the first cell
    ('ALIGNMENT',       (0,0),  (0,0),  'LEFT'), 
])

header = Table(header_data, colWidths=[inch*1.2, None, 0.6*inch], style=header_style)

# The text of the story
story = Paragraph(story_info['summary'], styles['BodyText'])

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
            size = 14
        
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
    [PullBox(checkbox_width, inch*0.25, 1),],
    [PullBox(checkbox_width, inch*0.25, 2),],
    [PullBox(checkbox_width, inch*0.25, 3),],
]

interrupted_table = Table(interrupted_data)

blocked_data = [
    [PullBox(checkbox_width, inch*0.25, 1, align="right"),],
    [PullBox(checkbox_width, inch*0.25, 2, align="right"),],
    [PullBox(checkbox_width, inch*0.25, 3, align="right"),],
]

blocked_table = Table(blocked_data)

checkboxes = Table(
    [[interrupted_table, blocked_table],],
    style=NoPadding,
)

main.addFromList(
    [
        header,
        story
    ],
    canvas
)

# use translate to get the checkboxes to always render at the bottom of the
# page, even if the summary text is short.
checkboxes_width, checkboxes_height  = checkboxes.wrap(frame_width, frame_height)

canvas.translate(0,-checkboxes_height)
main.addFromList([checkboxes,], canvas)

canvas.save()




