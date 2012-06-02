"""
Component architecture testing
"""
from zope import interface, component
from zope.component.factory import Factory, IFactory

class IGreeter(interface.Interface):
    """
    Create a dummy interface to identify our classes
    """
    def greet():
        "say hello"

class Greeter:
    """
    First class - standard implementation
    """
    interface.implements(IGreeter)
    
    def __init__(self, other="world"):
        self.other = other
    
    def greet(self):
        print "Hello", self.other

class Greeter2:
    """
    Second class - different implementation
    """
    interface.implements(IGreeter)
    
    def __init__(self, other="world"):
        self.other = other
    
    def greet(self):
        print "Goodbye", self.other
        

class IRudeGreeter(interface.Interface):
    """
    A greeter that isn't so nice.
    """

class RudeGreeter:
    """
    Third class - only implement the part we want to override,
    and adapt it to Greeter.
    """
    interface.implements(IGreeter)
    component.adapts(IRudeGreeter)
    
    def greet(self):
        print "%s is a jerk!" % (self.other)
    

# utilities
hello = Greeter()
goodbye = Greeter2()
        
component.provideUtility(hello, IGreeter, 'hello')
component.provideUtility(goodbye, IGreeter, 'goodbye')

utilities = component.getAllUtilitiesRegisteredFor(IGreeter)


# factories - this looks like the best way to proceed with registering
# renderers.
factory = Factory(Greeter, 'Greeter', 'Greeter Class, says hello')
factory2 = Factory(Greeter2, 'Greeter2', 'Greeter Class, says goodbye')

component.provideUtility(factory, IFactory, 'hello1')
component.provideUtility(factory2, IFactory, 'hello2')

factories = component.getFactoriesFor(IGreeter)

# adapters - no love
component.provideAdapter(
    factory=RudeGreeter,
    adapts=[IRudeGreeter],
    provides=IGreeter)


