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
""" Transitions in a web-configurable workflow.
"""

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from Persistence import PersistentMapping

from Products.CMFCore.Expression import Expression
from Products.CMFCore.permissions import ManagePortal

from .ContainerTab import ContainerTab
from .Guard import Guard
from .utils import _dtmldir


TRIGGER_AUTOMATIC = 0
TRIGGER_USER_ACTION = 1


class TransitionDefinition(SimpleItem):

    """Transition definition"""

    meta_type = 'Workflow Transition'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    title = ''
    description = ''
    new_state_id = ''
    trigger_type = TRIGGER_USER_ACTION
    guard = None
    actbox_name = ''
    actbox_url = ''
    actbox_icon = ''
    actbox_category = 'workflow'
    var_exprs = None  # A mapping.
    script_name = None  # Executed before transition
    after_script_name = None  # Executed after transition

    manage_options = (
        {'label': 'Properties', 'action': 'manage_properties'},
        {'label': 'Variables', 'action': 'manage_variables'})

    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id

    def getGuardSummary(self):
        res = None
        if self.guard is not None:
            res = self.guard.getSummary()
        return res

    def getGuard(self):
        if self.guard is not None:
            return self.guard
        else:
            return Guard().__of__(self)  # Create a temporary guard.

    def getVarExprText(self, id):
        if not self.var_exprs:
            return ''
        else:
            expr = self.var_exprs.get(id, None)
            if expr is not None:
                return expr.text
            else:
                return ''

    def getWorkflow(self):
        return aq_parent(aq_inner(aq_parent(aq_inner(self))))

    def getAvailableStateIds(self):
        return self.getWorkflow().states.keys()

    def getAvailableScriptIds(self):
        return self.getWorkflow().scripts.keys()

    def getAvailableVarIds(self):
        return self.getWorkflow().variables.keys()

    _properties_form = DTMLFile('transition_properties', _dtmldir)

    def manage_properties(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._properties_form(REQUEST,
                                     management_view='Properties',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    def setProperties(self, title, new_state_id,
                      trigger_type=TRIGGER_USER_ACTION, script_name='',
                      after_script_name='',
                      actbox_name='', actbox_url='',
                      actbox_category='workflow', actbox_icon='',
                      props=None, REQUEST=None, description=''):
        '''
        '''
        self.title = str(title)
        self.description = str(description)
        self.new_state_id = str(new_state_id)
        self.trigger_type = int(trigger_type)
        self.script_name = str(script_name)
        self.after_script_name = str(after_script_name)
        g = Guard()
        if g.changeFromProperties(props or REQUEST):
            self.guard = g
        else:
            self.guard = None
        self.actbox_name = str(actbox_name)
        self.actbox_url = str(actbox_url)
        self.actbox_icon = str(actbox_icon)
        self.actbox_category = str(actbox_category)
        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

    _variables_form = DTMLFile('transition_variables', _dtmldir)

    def manage_variables(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._variables_form(REQUEST,
                                    management_view='Variables',
                                    manage_tabs_message=manage_tabs_message)

    def getVariableExprs(self):
        ''' get variable exprs for management UI
        '''
        ve = self.var_exprs
        if ve is None:
            return []
        else:
            ret = []
            for key in ve.keys():
                ret.append((key, self.getVarExprText(key)))
            return ret

    def getWorkflowVariables(self):
        ''' get all variables that are available form
            workflow and not handled yet.
        '''
        wf_vars = self.getAvailableVarIds()
        if self.var_exprs is None:
            return wf_vars
        ret = []
        for vid in wf_vars:
            if vid not in self.var_exprs:
                ret.append(vid)
        return ret

    def addVariable(self, id, text, REQUEST=None):
        '''
        Add a variable expression.
        '''
        if self.var_exprs is None:
            self.var_exprs = PersistentMapping()

        expr = None
        if text:
            expr = Expression(str(text))
        self.var_exprs[id] = expr

        if REQUEST is not None:
            return self.manage_variables(REQUEST, 'Variable added.')

    def deleteVariables(self, ids=[], REQUEST=None):
        ''' delete a WorkflowVariable from State
        '''
        ve = self.var_exprs
        for id in ids:
            if id in ve:
                del ve[id]

        if REQUEST is not None:
            return self.manage_variables(REQUEST, 'Variables deleted.')

    def setVariables(self, ids=[], REQUEST=None):
        ''' set values for Variables set by this state
        '''
        if self.var_exprs is None:
            self.var_exprs = PersistentMapping()

        ve = self.var_exprs

        if REQUEST is not None:
            for id in ve.keys():
                fname = 'varexpr_%s' % id

                val = REQUEST[fname]
                expr = None
                if val:
                    expr = Expression(str(REQUEST[fname]))
                ve[id] = expr

            return self.manage_variables(REQUEST, 'Variables changed.')


InitializeClass(TransitionDefinition)


class Transitions(ContainerTab):

    """A container for transition definitions"""

    meta_type = 'Workflow Transitions'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    all_meta_types = ({'name': TransitionDefinition.meta_type,
                       'action': 'addTransition',
                       'permission': ManagePortal},)

    _manage_transitions = DTMLFile('transitions', _dtmldir)

    def manage_main(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._manage_transitions(
            REQUEST,
            management_view='Transitions',
            manage_tabs_message=manage_tabs_message,
            )

    def addTransition(self, id, REQUEST=None):
        '''
        '''
        tdef = TransitionDefinition(id)
        self._setObject(id, tdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Transition added.')

    def deleteTransitions(self, ids, REQUEST=None):
        '''
        '''
        for id in ids:
            self._delObject(id)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Transition(s) removed.')


InitializeClass(Transitions)
