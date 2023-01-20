##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""DCWorkflow interfaces.
"""

from zope.interface import Attribute
from zope.interface import Interface
from zope.interface.interfaces import IObjectEvent


class IDCWorkflowDefinition(Interface):

    """Web-configurable workflow definition.
    """


class ITransitionEvent(IObjectEvent):

    """An event that's fired upon a workflow transition.
    """

    workflow = Attribute("The workflow definition triggering the transition")
    old_state = Attribute("The state definition of the workflow state "
                          "before the transition")
    new_state = Attribute("The state definition of the workflow state "
                          "before after transition")
    transition = Attribute("The transition definition taking place. "
                           "May be None if this is the 'transition' to the "
                           "initial state.")
    status = Attribute("The status dict of the object.")
    kwargs = Attribute("Any keyword arguments passed to doActionFor() when "
                       "the transition was invoked")


class IBeforeTransitionEvent(ITransitionEvent):

    """An event fired before a workflow transition.
    """


class IAfterTransitionEvent(ITransitionEvent):

    """An event that's fired after a workflow transition.
    """
