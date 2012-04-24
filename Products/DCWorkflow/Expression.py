##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Expressions in a web-configurable workflow.
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from DateTime.DateTime import DateTime
from MultiMapping import MultiMapping
from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter

from Products.CMFCore.Expression import Expression # BBB: old location
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.WorkflowCore import ObjectDeleted
from Products.CMFCore.WorkflowCore import ObjectMoved


class SafeMapping(MultiMapping):

    """Mapping with security declarations and limited method exposure.

    Since it subclasses MultiMapping, this class can be used to wrap
    one or more mapping objects.  Restricted Python code will not be
    able to mutate the SafeMapping or the wrapped mappings, but will be
    able to read any value.
    """
    __allow_access_to_unprotected_subobjects__ = 1
    push = pop = None
    _push = MultiMapping.push
    _pop = MultiMapping.pop


class StateChangeInfo(object):

    '''
    Provides information for expressions and scripts.
    '''
    _date = None

    ObjectDeleted = ObjectDeleted
    ObjectMoved = ObjectMoved

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')

    def __init__(self, object, workflow, status=None, transition=None,
                 old_state=None, new_state=None, kwargs=None):
        if kwargs is None:
            kwargs = {}
        else:
            # Don't allow mutation
            kwargs = SafeMapping(kwargs)
        if status is None:
            tool = aq_parent(aq_inner(workflow))
            status = tool.getStatusOf(workflow.id, object)
            if status is None:
                status = {}
        if status:
            # Don't allow mutation
            status = SafeMapping(status)
        self.object = object
        self.workflow = workflow
        self.old_state = old_state
        self.new_state = new_state
        self.transition = transition
        self.status = status
        self.kwargs = kwargs

    def __getitem__(self, name):
        if name[:1] != '_' and hasattr(self, name):
            return getattr(self, name)
        raise KeyError(name)

    def getHistory(self):
        wf = self.workflow
        tool = aq_parent(aq_inner(wf))
        wf_id = wf.id
        h = tool.getHistoryOf(wf_id, self.object)
        if h:
            return map(lambda dict: dict.copy(), h)  # Don't allow mutation
        else:
            return ()

    def getPortal(self):
        ob = aq_inner(self.object)
        while ob is not None:
            if ISiteRoot.providedBy(ob):
                return ob
            ob = aq_parent(ob)
        return None

    def getDateTime(self):
        date = self._date
        if not date:
            date = self._date = DateTime()
        return date

InitializeClass(StateChangeInfo)


def createExprContext(sci):
    '''
    An expression context provides names for TALES expressions.
    '''
    ob = sci.object
    wf = sci.workflow
    container = aq_parent(aq_inner(ob))
    data = {
        'here':         ob,
        'object':       ob,
        'container':    container,
        'folder':       container,
        'nothing':      None,
        'root':         ob.getPhysicalRoot(),
        'request':      getattr(ob, 'REQUEST', None),
        'modules':      SecureModuleImporter,
        'user':         getSecurityManager().getUser(),
        'state_change': sci,
        'transition':   sci.transition,
        'status':       sci.status,
        'kwargs':       sci.kwargs,
        'workflow':     wf,
        'scripts':      wf.scripts,
        }
    return getEngine().getContext(data)
