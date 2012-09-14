"""
Service that generates (and serves) thumbnail images from printable files

:todo: shelling out to ImageMagick now to create the thumbnails - not sure how
       scalable that is, it might be a good idea to use another mechanism
"""

from twisted.web.server import NOT_DONE_YET
from . import ConfigurableSite
from twisted.internet.threads import deferToThread
from twisted.web.resource import Resource
from twisted.internet import inotify
from twisted.python import filepath

class ThumbnailService(ConfigurableSite):
    """
    
    """
    
