"""
Resources for the HTML Front-end to the RESTful API
"""
from twisted.web.static import File
from twisted.web.resource import Resource
import pkg_resources

from .. import static_path, templates
from . import JinjaTemplateResource

StaticFiles = File(static_path)
StaticFiles.putChild("deform", File(pkg_resources.resource_filename("deform", "/static")))

class Main(JinjaTemplateResource):
    """
    Render the main UI screen.
    """
    isLeaf = True
    
    template = templates.get_template('ui-main.jinja2')
    
    def render_GET(self, request):
        
        self._data = {
            'request': request,
            'print_service_uri': "http://%s:%s" % (request.host.host, request.transport.protocol.factory.settings['print_service_port']),
        }
        return self.render_template(request)
