from zope.interface import implements
from zope.component.interfaces import ObjectEvent

from interfaces import ITransitionEvent, IBeforeTransitionEvent, IAfterTransitionEvent

class TransitionEvent(ObjectEvent):
    implements(ITransitionEvent)
    
    def __init__(self, obj, workflow, old_state, new_state, transition, status, kwargs):
        ObjectEvent.__init__(self, obj)
        self.workflow = workflow
        self.old_state = old_state
        self.new_state = new_state
        self.transition = transition
        self.status = status
        self.kwargs = kwargs
        
class BeforeTransitionEvent(TransitionEvent):
    implements(IBeforeTransitionEvent)
    
class AfterTransitionEvent(TransitionEvent):
    implements(IAfterTransitionEvent)