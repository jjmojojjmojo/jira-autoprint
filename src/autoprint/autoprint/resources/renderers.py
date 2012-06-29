"""
Resources related to the renderer API
"""

from . import JinjaTemplateResource, JSONResource
from .. import templates
from ..session import IPrintedFiles, PrintedFiles

import json, uuid
from twisted.web.server import NOT_DONE_YET
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
from twisted.web.static import File, NoRangeStaticProducer
from twisted.python.filepath import FilePath
from twisted.web.error import NoResource
from deform import Form, ValidationFailure
import colander
from datetime import datetime

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

class RendererForm(Resource):
    """
    GET: render the schema into an HTML form (uses: mod:`deform`).
    POST: render the schema into an HTML form with the provided values.
    """
    isLeaf = True
    
    def __init__(self, renderer):
        self._renderer = renderer
        
        Resource.__init__(self)
    
    def render(self, request):
        request.setHeader('access-control-allow-origin', request.getHeader('origin'))
        request.setHeader('access-control-allow-credentials', 'true')
        
        return Resource.render(self, request)
    
    def _form(self, request):
        """
        Build a form from the request.
        
        Uses request variables to populate the buttons and action if specified
        """
        buttons = request.args.get('_button', ())
        action = request.args.get('_action', [""])[0]
        
        form = Form(self._renderer.schema, buttons=buttons, action=action)
        
        return form
    
    def render_GET(self, request):
        form = self._form(request)
        
        return form.render().encode('utf-8')
        
    def render_POST(self, request):
        appstruct = colander.null
        
        form = self._form(request)
        
        data = flatten_args(request)
        
        output = ''
        
        try:
            appstruct = form.validate(data)  # call validate
            output = form.render(appstruct)
        except ValidationFailure, e: # catch the exception
            form = e # re-render the form with errors pointed out
            request.setResponseCode(400)
            output = form.render()
        
        request.write(output.encode('utf-8'))
        request.finish()
        
        return NOT_DONE_YET

class Renderer(JSONResource):
    """
    GET: Returns a renderer dumped as JSON.
    POST: Runs the renderer (JSON body expected), returns a URL to download the file.
    PUT: runs the renderer and sends it off to CUPs
    """
    
    def __init__(self, renderer):
        self._data = renderer
        self._renderer = renderer
        
        JSONResource.__init__(self)
    
    def getChild(self, name, request):
        """
        Overload getChild to pick up a request for a RendererForm
        """
        session = request.getSession()
        
        if name == 'form':
            return RendererForm(self._renderer)
        else:
            info = IPrintedFiles(session)
            
            to_serve = info.get(name, {'filename':None})
            
            if to_serve['filename']:
                return File(to_serve)
            else:
                return NoResource()     
                
    
    def _render(self, request):
        """
        Run the data supplied by the client through the Renderer
        """
        schema = self._renderer.schema
        session = request.getSession()
        try:
            appstruct = schema.deserialize(self._data)
            filename = self._renderer(appstruct)
            
            info = IPrintedFiles(session)
            
            unique_id = str(uuid.uuid4().hex)
            
            info[unique_id] = {
                'filename': filename,
                'printed': datetime.now(),
                'ip': request.getClientIP(),
                'renderer': self._renderer.title,
            }
            
            if request.method == 'POST':
                self._data = {'printed': unique_id}
            else:
                # PUT
                d = request.transport.protocol.factory.printFile(filename, self._renderer.title)
                
                def result(jobid):
                    self._data = {
                        'printed': unique_id,
                        'job_id': jobid,
                    }
                    
                    return self.render_GET(request)
                    
                d.addCallback(result)
                
                return NOT_DONE_YET
            
        except colander.Invalid, e:
            request.setResponseCode(400)
            self._data = e.asdict()
            return self.render_GET(request)
    
    def render_POST(self, request):
        """
        Receive a post (with a JSON body) and return an id the client can use
        to retrieve the printable file.
        
        If there is a validation error, a 400 status is returned, along with a 
        JSON structure containing error details
        
        """
        return self._render(request)
            
    def render_PUT(self, request):
        """
        Recieve a PUT (with a JSON body) and send it to CUPS
        """
        return self._render(request)
        
    
class RendererList(JSONResource):
    """
    Returns a list of renderers as JSON
    """
        
    def _adjust_data(self, request):
        self._data = []
            
        renderers = request.transport.protocol.factory.renderers
        
        for name, renderer in renderers.iteritems():
            self._data.append({
                 'name': name,
                 'title': renderer.title,
                 'description': renderer.description,
            })

class RendererPrintedList(JSONResource):
    """
    Returns a dictionary of printed items via JSON
    """
    def _adjust_data(self, request):
        info = IPrintedFiles(session)
        self._data = info
    

class RendererAPI(Resource):
    """
    /renderers - GET, list of available renderers (JSON)
    /renderers/[name] - GET, JSON representing the given renderer
                        POST, preview renderer
                        PUT, print renderer
    /renderers/[name]/form - GET, HTML rendering of a deform form.
    """
    
    def render_GET(self, request):
        listing = RendererList()
        
        return listing.render(request)
    
    def getChild(self, name, request):
        """
        Overload getChild to dispatch to the proper url mapping
        """
        if name:
            renderers = request.transport.protocol.factory.renderers
            
            renderer = renderers.get(name, None)
            
            if not renderer:
                return NoResource()
            
            return Renderer(renderer)
        else:
            return RendererList()
