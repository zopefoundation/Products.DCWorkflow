# -*- coding: utf-8 -*-
from zope.interface import implementer
from zope.component.interfaces import ObjectEvent

from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from Products.DCWorkflow.interfaces import IBeforeTransitionEvent
from Products.DCWorkflow.interfaces import ITransitionEvent


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
