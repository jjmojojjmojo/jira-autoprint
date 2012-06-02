"""
Schema Comparison
"""

from zope.interface import Interface, implements, Attribute
import zope.schema, zope.component

import colander

############################
#
# zope.schema
#

class IRenderer(Interface):
    """
    Receives structured data from the print service, renders a PDF or other
    printable file to disk, and then returns the path so it can be passed on
    to CUPS
    """
    
    title = Attribute("Brief, but descriptive title for this renderer")
    settings = Attribute("Dictionary of lookup lists and other infrequently-configured settings, that can be overridden at run-time")
    
    def __call__(data):
        """
        Given the data, generate a printable file and return the path to it.
        """

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
    
######################
#
# Colander
#

class RendererSchema(colander.MappingSchema):
    """
    Defines necessary data needed by all renderers. 
    """
    
    summary = colander.SchemaNode(
        colander.String(),
        title=u"Summary",
        description=u"A one-sentence description of the issue",
    )
    
    detail = colander.SchemaNode(
        colander.String(),
        title=u"Details",
        description=u"Elaborated details about the issue.",
    )
    
    issue_id = colander.SchemaNode(
        colander.String(),
        title=u"Identifier",
        description=u"A (probably) unique identifier that this issue is known by",
    )
    
    issue_type = colander.SchemaNode(
        colander.String(), 
        validator=colander.OneOf((
            u'Operational Task',
            u'Task'
            u'Story'
            u'Epic'
            u'Improvement',
            u'Bug',
            u'Unknown',
        )),
        missing = u'Unknown',
    )
    
    reporter = colander.SchemaNode(
        colander.String(),
        title=u"Reporter",
        description=u"The name of the person who reported this issue",
    )
    
    date = colander.SchemaNode(
        colander.DateTime(),
        title=u"Date",
        description=u"The date/time that the issue was created, or modified",
    )
    
    priority = colander.SchemaNode(
        colander.String(), 
        validator=colander.OneOf((
            u'Blocker',
            u'Critical',
            u'Major',
            u'Minor',
            u'Trivial',
            u'Unknown',
        )),
        title=u"Priority",
        description=u"How urgent is this issue?",
        missing = u'Unknown',
    )
    
    border = colander.SchemaNode(
        colander.Boolean(), 
        title=u"Draw Border?",
        description=u"Should a border be drawn around the perimeter of the card?",
        missing = True,
    )
