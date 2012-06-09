"""
Common utilities
"""
from twisted.web.resource import Resource

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
