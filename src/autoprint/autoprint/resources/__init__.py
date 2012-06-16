"""
Resource objects used by Sites

Common base classes live in this file.
"""
from twisted.web.resource import Resource
from twisted.internet.threads import deferToThread
from twisted.internet import defer
from twisted.web.server import NOT_DONE_YET
import json

class JinjaTemplateResource(Resource):
    """
    Add jinja2 template processing functionality
    """
    template = None # a Jinja2 template object - instantiate when building the class
    
    _data = None # dictionary of values to pass to the template 
    
    def _render_template(self, request):
        """
        Callback to render the primary template from a deferred.
        """
        request.write(self.template.render(self._data).encode('utf-8'))
        request.finish()
        
    def render_template(self, request):
        """
        Render the primary template, deferred to a thread
        """
        d = deferToThread(self._render_template, request)
        return NOT_DONE_YET
        
class ResourceEncoder(json.JSONEncoder):
    """
    Custom encoder that flattens out objects in a sane way
    """
    
    def default(self, obj):
        """
        Override default to provide a __json__ property. It's expected
        to be a dictionary (or other json serializable object).
        """
        
        try:
            return obj.__json__
        except AttributeError:
            pass
        
        return json.JSONEncoder.default(self, obj)

class JSONResource(Resource):
    """
    Marshalls JSON data in the _data dictionary.
    
    If the request is a POST or PUT, it populates the dictionary with the decoded
    data prior to calling the usual handlers.
    
    By default, if the request is a GET, it dumps the content of _data into the
    response and sets the proper header.
    """
    
    _data = None
    
    def _adjust_data(self, request=None):
        """
        Called by render() after deserializing the JSON, so subclassing classes
        can manipulate or add to the _data property.
        
        Can return a deferred if necessary.
        """
        pass
    
    def render(self, request):
        request.setHeader('access-control-allow-origin', request.getHeader('origin'))
        request.setHeader('access-control-allow-credentials', 'true')
        request.setHeader("access-control-allow-methods", "POST, GET, OPTIONS, PUT")
        request.setHeader("access-control-max-age", "1728000")
        request.setHeader("access-control-allow-headers",  "content-type")

        
        if request.method in ('POST', 'PUT'):
            self._data = json.loads(request.content.getvalue())

        d = defer.maybeDeferred(self._adjust_data, request)
        
        def do_render(info):
            Resource.render(self, request)
        
        d.addCallback(do_render)
        
        return NOT_DONE_YET
        
    def render_GET(self, request):
        request.setHeader('content-type', 'application/json')
        
        request.write(json.dumps(self._data, sort_keys=True, indent=4, cls=ResourceEncoder))
        request.finish()
        
    def render_OPTIONS(self, request):
        
        request.setResponseCode(200)
        
        request.setHeader('content-type', 'text/plain')
        
        request.finish()

   
