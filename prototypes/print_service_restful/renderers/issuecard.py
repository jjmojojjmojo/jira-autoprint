from zope.interface import Interface, implements, Attribute
import zope.schema, zope.component
from zope.component.factory import Factory, IFactory

import tempfile

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, Table, TableStyle, KeepInFrame
from reportlab.platypus.flowables import XBox, Image
from reportlab.pdfgen.canvas import Canvas 
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.pdfbase.pdfmetrics import stringWidth, getFont
from reportlab.lib.colors import pink, black, red, blue, green, lightgrey, darkgrey

from .util import PullBox
from . import IRenderer

class IIssueCardRenderer(IRenderer):
    """
    Generic issue/bug/task on an index card.
    
    :todo: migrate the Choice fields to use the settings attribute as a vocabulary.
    """
    summary = zope.schema.Text(
        title=u"Summary",
        description=u"A one-sentence description of the issue",
        default=u"",
    )
    
    detail = zope.schema.Text(
        title=u"Details",
        description=u"Elaborated details about the issue.",
        default=u"",
    )
    
    issue_id = zope.schema.TextLine(
        title=u"Identifier",
        description=u"A (probably) unique identifier that this issue is known by",
        default=u"",
    )
    
    issue_type = zope.schema.Choice(
        values=(
            u'Operational Task',
            u'Task'
            u'Story'
            u'Epic'
            u'Improvement',
            u'Bug',
            u'Unknown',
        ),
        title=u"Issue Type",
        description=u"The type of issue.",
        default=u"Unknown",
    )
    
    reporter = zope.schema.TextLine(
        title=u"Reporter",
        description=u"The name of the person who reported this issue",
        default=u"Unknown",
    )
    
    date = zope.schema.Datetime(
        title=u"Date",
        description=u"The date/time that the issue was created, or modified",
    )
    
    priority = zope.schema.Choice(
        values=(
            u'Blocker',
            u'Critical',
            u'Major',
            u'Minor',
            u'Trivial',
            u'Unknown',
        ),
        title=u"Priority",
        description=u"How urgent is this issue?",
        default=u"Unknown",
    )
    
    border = zope.schema.Bool(
        title=u"Draw Border?",
        description=u"Should a border be drawn around the perimeter of the card?",
        default=True,
    )

class IssueCardRenderer:
    """
    Renders a generic card that can be used for any bug tracking or other issue
    system.
    """
    
    implements(IIssueCardRenderer)
    
    title = "Generic Issue/Bug/Story"
    settings = {
        'icons': {
            'Operational Task': 'images/cards-heart.png',
            'Task': 'images/agt_utilities.png',
            'Story': 'images/agt_utilities.png',
            'Epic': 'images/agt_utilities.png',
            'Improvement': 'images/agt_utilities.png',
            'Bug': 'images/tools-report-bug.png',
            'Unknown': 'images/agt_utilities.png',
        },
        
        'priority_icons': {
            'Blocker': 'images/software-update-urgent-2.png',
            'Critical': 'images/emblem-important-3.png',
            'Major': 'images/emblem-special.png',
            'Minor': 'images/emblem-generic.png',
            'Trivial': 'images/emblem-generic.png',
            'Unknown': 'images/face-uncertain.png',
        },
        
        'priority_colors': {
            'Blocker': '#F56C6C',
            'Critical':  '#F56C6C',
            'Major':  '#EEEEEE',
            'Minor': '#CEE8F0',
            'Trivial': '#CEE8F0',
            'Unknown': '#FFFFFF',
        },
        
        'pagesize':(5*inch, 3*inch),
        
        'font':"Helvetica",
        'fontSize':12,
        'margin':inch*0.15,
    }
    
    def __init__(self, **settings):
        """
        Settings will be applied onto the :attr:`settings` property.
        """
        
        self.settings.update(settings)
        
        junk, self.output = tempfile.mkstemp(suffix=".pdf")
     
    def _getStyleSheet(self):
        """
        Generate a custom stylesheet
        
        :todo: build styles for every element instead of hard coding
        """
        styles = getSampleStyleSheet()
        styles['Normal'].fontName = "Helvetica"
        styles['BodyText'].fontSize = 12
        
        return styles
        
    def __call__(self, data):
        """
        Generate the PDF
        """
        icon = self.settings['icons'].get(data['issue_type'], self.settings['icons']['Unknown'])
        priority_icon = self.settings['priority_icons'].get(data['priority'], self.settings['priority_icons']['Unknown'])
        
        styles = self._getStyleSheet()
        
        canvas = Canvas(self.output, pagesize=self.settings['pagesize'])
        
        margin = self.settings['margin']
        page_width, page_height = self.settings['pagesize']
        
        frame_width = page_width-(margin*2)
        frame_height = page_height-(margin*2)
        
        main = Frame(margin, margin, frame_width, frame_height, showBoundary=0, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
        footer = Frame(margin, margin, frame_width, frame_height, showBoundary=0, leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
        
        if data['border']:
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
              Image(icon, inch*0.4, inch*0.4),
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
              Image(priority_icon, inch*0.4, inch*0.4),
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
        story = Paragraph("<b>"+data['summary']+"</b>", styles['BodyText'])
        
        # the text of the description - just the first 20 words 
        detail_words = data['detail'].split()
        
        short_detail = " ".join(detail_words[:50])
        
        if len(detail_words) > 50:
            short_detail += '...'
        
        details = KeepInFrame(frame_width, frame_height/3, [Paragraph(short_detail, styles['BodyText']),], mode="shrink", mergeSpace=0)
        
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
        
        canvas.save()
        
        return self.output

# register the factories in the component architecture.
factory = Factory(IssueCardRenderer, 'Generic Issue Card Renderer', IssueCardRenderer.__doc__)

zope.component.provideUtility(factory, IFactory, 'issuecardrenderer')
