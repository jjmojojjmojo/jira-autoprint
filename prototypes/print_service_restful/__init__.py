"""
Rewrite of the print service as a RESTful API using twisted.web
"""

from twisted.web.server import Site, NOT_DONE_YET
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.static import File, NoRangeStaticProducer
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
import cups, pprint, os
from .renderers import IRenderer

from deform import Form, ValidationFailure
import colander

import pkg_resources

from zope.component import getFactoriesFor, createObject

from jinja2 import Environment, FileSystemLoader

template_path = os.path.join(os.path.dirname(__file__), 'templates')

static_path = os.path.join(template_path, 'static')

templates = Environment(loader=FileSystemLoader(template_path))

class JinjaTemplateResource(Resource):
    """
    Add jinja2 template processing functionality
    """
    template = None # a Jinja2 template object - instantiate when building the class
    
    def _render_template(self, data, request):
        """
        Callback to render the primary template from a deferred.
        """
        request.write(self.template.render(data).encode('utf-8'))
        request.finish()
        
    def render_template(self, data, request):
        """
        Render the primary template, deferred to a thread
        """
        d = deferToThread(self._render_template, data, request)
        return NOT_DONE_YET

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
    

def renderer_form(request, renderer=None, load=False):
    """
    Render a given form 
    
    :param: request - a twisted.web.request object
    :param: renderer - the name of the renderer you want to use
    :param: load - boolean, set to True to attempt to deserialize the data from the request
    """
    if not renderer:
        # request.setResponseCode(402)
        return "No renderer exists"
        
    
    renderer_id = request.args.get('__renderer', [None])[0]
    
    form = Form(renderer.schema, buttons=('Preview', 'Print'), action="?__renderer=%s" % (renderer_id))
    
    if load:
        try:
            data = flatten_args(request)
            appstruct = form.validate(data)  # call validate
            output = form.render(appstruct)
        except ValidationFailure, e: # catch the exception
            output = e.render() # re-render the form with an exception
    else:
        output = form.render()
        
    return output.encode('utf-8')

class RendererForm(Resource):
    """
    Common functions for Renderer form-related resources
    """
    def _flatten(self, request):
        """
        Translate a Request object into something that deform can consume.
        """
        output = []
    
        for field, values in request.args.iteritems():
            for val in values:
                output.append((field, val))
                
        return output
    
    def _renderer(self, request):
        """
        Given a Request object, return a two-tuple:
         (renderer object or None, id asked for or None)
        """
        asked_for = request.args.get('__renderer', [None])[0]
    
        renderer = None
    
        if asked_for:
            renderer = request.transport.protocol.factory.renderers.get(asked_for, None)
            
        return (renderer, asked_for)
    
    def _form(self, renderer, renderer_id):
        """
        Build a deform Form() object for a given renderer object.
        """
        form = Form(renderer.schema, buttons=('Preview', 'Print'), action="?__renderer=%s" % (renderer_id))
        
        return form
    
    def _initial_form(self, request):
        """
        Return a blank form for the given renderer.
        
        If renderer is None, returns a notice string
        """
        (renderer, asked_for) = self._renderer(request)
        
        if not renderer:
            return "Unknown or unspecified renderer"
        
        
        form = self._form(renderer, asked_for)
        
        return form
        
    def _validate_form(self, request):
        """
        Return a processed version of the renderer form, and a flag to indicate
        if there is an error.
        """
        
        form = self._initial_form(request)
        
        output = ""
        status = 'ok'
        appstruct = colander.null
        
        try:
            data = flatten_args(request)
            appstruct = form.validate(data)  # call validate
            
        except ValidationFailure, e: # catch the exception
            form = e # re-render the form with an exception
            status = 'error'
            
        return (form, status, appstruct)
    

class FetchRendererForm(RendererForm):
    """
    Returns a rendered deform form for a given Renderer object
    
    Expected to be called via AJAX and inserted into a page with the proper javascript
    and CSS pre-loaded.
    """
    def render_GET(self, request):
        form = self._initial_form(request)
        
        return form.render().encode('utf-8')
    


class PrintDocument(JinjaTemplateResource, RendererForm):
    """
    GET - return a form where the user can punch in some values for the 
          renderer
          
    POST - return the rendered PDF
    PUT - send the PDF to the printer
    """
    
    template = templates.get_template('print.jinja2')
    
    def _context(self, request):
        """
        Common data structure passed to the template during GET and post
        """
        (renderer, asked_for) = self._renderer(request)
        
        data = {
            'request': request,
            'renderer_form': None,
            'renderers': request.transport.protocol.factory.renderers,
            'selected_renderer': asked_for,
            'renderer': renderer,
        }
        
        return data
        
    
    def render_GET(self, request):
        
        context = self._context(request)
        
        if context['selected_renderer']:
            context['renderer_form'] = self._initial_form(request)
        
        self.render_template(context, request)
        
        return NOT_DONE_YET

        
    def render_POST(self, request):
        
        context = self._context(request)
        
        form, status, appstruct = self._validate_form(request)
        
        if status == 'ok':
            filename = context['renderer'](appstruct)
            
            fileobj = FilePath(filename)
            
            request.setHeader('content-disposition', 'attachment; filename="output.pdf"')
            request.setHeader('content-length', str(fileobj.getsize()))
            request.setHeader('content-type', 'application/pdf')
            
            producer = NoRangeStaticProducer(request, fileobj.open('r'))
            
            producer.start()
            
            return NOT_DONE_YET
        
        data['renderer_form'] = form.render(appstruct)
        
        self.render_template(data, request)
        
        return NOT_DONE_YET
        
    def render_PUT(self, request):
        return "putted"
    
class PrinterStatus(JinjaTemplateResource):
    """
    GET - display the current status of the CUPS print queue.
    """
    isLeaf = True
    
    template = templates.get_template('status.jinja2')
    
    def render_GET(self, request):
        d = request.transport.protocol.factory.CUPSPrinterStatus()
        
        def _finish_status(info):
            data = {
                'request': request,
                'attributes': pprint.pformat(info['attributes']),
                'printer': info['printer'],
            }
            
            self.render_template(data, request)
        
        d.addCallback(_finish_status)
        return NOT_DONE_YET

class PrintService(Site):
    def __init__(self, **kwargs):
        """
        :todo: read config file or pass other settings for things like 
               renderer settings.
        """
        
        root = Resource()
        root.putChild('status', PrinterStatus())
        root.putChild('static', File(static_path))
        root.putChild('deform', File(pkg_resources.resource_filename("deform", "/static")))
        root.putChild('renderer', FetchRendererForm())
        root.putChild('', PrintDocument())
        
        Site.__init__(self, root, **kwargs)
        
        self._connection = cups.Connection()
        self.renderers = self.loadRenderers()

    def _printerStatus(self):
        """
        Return a dictionary containing information about the current printer
        status.
        """
        printer = self._connection.getDefault()
        attributes = self._connection.getPrinterAttributes(printer)
        
        return {
            'printer': printer,
            'attributes': attributes,
        }
        
    def CUPSPrinterStatus(self):
        return deferToThread(self._printerStatus)
        
    def loadRenderers(self):
        """
        Return a list of renderer objects
        
        :todo: replace with call to :mod:`pkg_resources`
        """
        from renderers import CenteredPageRenderer, IssueCardRenderer
        
        renderers = {
            'centered': CenteredPageRenderer(),
            'issue': IssueCardRenderer(),
        }
            
        return renderers
        
