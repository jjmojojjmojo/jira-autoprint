"""
Service Status Resources
"""
from . import JinjaTemplateResource, JSONResource
from .. import templates

import json
from twisted.web.server import NOT_DONE_YET
from twisted.internet.threads import deferToThread

def service_status(request):
    """
    Return a dictionary of service status information.
    
    :todo: Add in other useful information
    """
    d = request.transport.protocol.factory.printerStatus()
    
    def renderers(data):
        renderers = request.transport.protocol.factory.renderers
        data['renderers'] = {}
        
        # convert the renderers into something serializable
        for name, renderer in renderers.iteritems():
            data['renderers'][name] = {
                 'title': renderer.title,
                 'description': renderer.description,
            }
        
        return data
    
    d.addCallback(renderers)
    
    return d

class ServiceStatus(JinjaTemplateResource):
    """
    Display useful status information about the 
    print service
    """
    isLeaf = True
    
    template = templates.get_template('appstatus.jinja2')
    
    def render_GET(self, request):
        d = service_status(request)
        
        def go(data):
            self._data = data
            self.render_template(request)
        
        d.addCallback(go)
        
        return NOT_DONE_YET
        
class ServiceStatusJSON(JSONResource):
    """
    Alternate ServiceStatus
    
    Returns a JSON serialized body and sets the right header for JSON content
    
    :todo: should this data be sanitized?
    """
    def _adjust_data(self, request):
        d = service_status(request)
        
        def go(data):
            self._data = data
        
        d.addCallback(go)
        
        return d
