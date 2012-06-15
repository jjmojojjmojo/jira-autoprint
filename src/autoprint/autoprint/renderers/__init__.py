"""
Common renderer classes and utilities.
"""

from zope.interface import Interface, implements, Attribute

import os, colander

image_path = os.path.join(os.path.dirname(__file__), 'images')

class IRenderer(Interface):
    """
    Receives structured data from the print service, renders a PDF or other
    printable file to disk, and then returns the path so it can be passed on
    to CUPS
    """
    
    title = Attribute("Brief, but descriptive title for this renderer")
    settings = Attribute("Dictionary of lookup lists and other infrequently-configured settings, that can be overridden at run-time")
    schema = Attribute("colander schema defining required inputs")
    content_type = Attribute("Mime-type for the type of printable object this renderer creates")
    __json__ = Attribute("Representation of this renderer that JSON can serialize")
    
    def __call__(data):
        """
        Given the data, generate a printable file and return the path to it.
        """

class Renderer(object):
    
    implements(IRenderer)
    
    title = None
    settings = None
    schema = None
    content_type = "application/pdf"
    
    def __init__(self, **settings):
        """
        Settings will be applied onto the :attr:`settings` property.
        """
        self.settings.update(settings)
    
    def __call__(data):
        pass
    
    @property
    def __json__(self):
        """
        Return a JSON-serializable object
        """
        return {
            'title': self.title,
            'description': self.description,
            'class': self.__class__.__name__,
            'settings': self.settings,
            'schema': colander_to_json_schema(self.schema),
        }
                
COLANDER_TO_JSON_TYPE_MAP = {
    'String': 'string',
    'Str': 'string',
    'Mapping': 'object',
    'Int': 'integer',
    'Integer': 'integer',
    'Tuple': 'array',
    'Float': 'number',
    'Decimal': 'number',
    'Boolean': 'boolean',
    'Bool': 'boolean',
    'Date': 'string',
    'DateTime': 'string',
    'Time': 'string',
    
}

def colander_to_json_schema(schema):
    """
    Transforms a :mod:`colander` schema into a JSON-schema string.
    
    :todo: Unit tests
    :todo: work with nested schemas
    """
    struct = {
        "description":schema.description,
        "type":"object",
        "properties": {}
    }
    
    for node in schema:
        colendar_type = node.typ.__class__.__name__
        type_ = COLANDER_TO_JSON_TYPE_MAP.get(colendar_type, 'string')
        
        
        
        struct['properties'][node.name] = dict(
            type=type_,
            required=node.required,
            default=node.default,
            title=node.title,
            description=node.description,
        )
        
        # JSON can't serialize the collander.null object
        if node.default is colander.null:
            struct['properties'][node.name]['default'] = None
        
        # set the format for date/time fields (they are stored as strings)
        if colendar_type == 'DateTime':
            struct['properties'][node.name]['format'] = 'date-time'
            
        if colendar_type == 'Time':
            struct['properties'][node.name]['format'] = 'time'
            
        if colendar_type == 'Date':
            struct['properties'][node.name]['format'] = 'date'
            
        # set the possibilities based on the validator, if its set
        if node.validator and isinstance(node.validator, colander.OneOf):
            struct['properties'][node.name]['enum'] = node.validator.choices
            
    return struct
    
def flatten_args(request):
    """
    Translate a twisted.web Request object's form variables into something
    that colendar can handle
    
    :todo: this feels hackish - is there a more elegant way? A more efficient one?
    """
    
    output = []
    
    for field, values in request.args.iteritems():
        for val in values:
            output.append((field, val))
            
    return output
