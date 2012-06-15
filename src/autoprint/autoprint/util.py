"""
Common utilities
"""
import pkg_resources

def loadRenderers():
    """
    Return a dictionary of all of the renderer objects installed.
    """
    entry_map = pkg_resources.get_entry_map('autoprint', 'autoprint.renderers')
    
    output = {}
    for name, entry in entry_map.iteritems():
        
        entry.require()
        
        class_ = entry.load()
        
        output[name] = class_()
        
    return output
