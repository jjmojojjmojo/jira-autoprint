"""
Services provided by this application.
"""

from twisted.web.server import Site
from twisted.web.resource import Resource

class ConfigurableSite(Site):
    """
    Base class that allows for custom configuration options that will not be passed
    on to the Site base class.
    
    :TODO: load settings from configparser-compatible file?
    """
    
    # a dictionary of settings passed to the constructor
    settings = None 
    
    # dictionary of class-specific configuration values - the keys of this
    # dictionary correspond to special configuration options that can be passed
    # to __init__, but aren't valid arguments to Site.__init__()
    _defaults = None
    
    def _filter_settings(self, kwargs):
        """
        Takes a dictionary of key-word arguments - sets self.settings, and returns
        a dictionary that can be passed directly as keyword arguments to Site.__init__().
        """
        self.settings = {}
        
        for key, default in self._defaults.iteritems():
            self.settings[key] = kwargs.get(key, default)
            
            try:
                del kwargs[key]
            except KeyError:
                pass
                
        return kwargs
    
    def root(self):
        """
        Expected to be overloaded by child classes - sets up the root resource 
        object passed to Site.__init__()
        """
        return Resource()
        
    def __init__(self, *args, **kwargs):
        kwargs = self._filter_settings(kwargs)
    
        Site.__init__(self, self.root(), **kwargs)
        
