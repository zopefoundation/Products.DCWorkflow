from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent

from .interfaces import IAfterTransitionEvent
from .interfaces import IBeforeTransitionEvent
from .interfaces import ITransitionEvent


@implementer(ITransitionEvent)
class TransitionEvent(ObjectEvent):

    def __init__(self, obj, workflow, old_state, new_state,
                 transition, status, kwargs):
        ObjectEvent.__init__(self, obj)
        self.workflow = workflow
        self.old_state = old_state
        self.new_state = new_state
        self.transition = transition
        self.status = status
        self.kwargs = kwargs


@implementer(IBeforeTransitionEvent)
class BeforeTransitionEvent(TransitionEvent):
    pass


@implementer(IAfterTransitionEvent)
class AfterTransitionEvent(TransitionEvent):
    pass
