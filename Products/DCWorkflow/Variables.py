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
""" Variables in a web-configurable workflow.

$Id$
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from zExceptions import BadRequest

from Products.CMFCore.Expression import Expression
from Products.DCWorkflow.ContainerTab import ContainerTab
from Products.DCWorkflow.Guard import Guard
from Products.DCWorkflow.permissions import ManagePortal
from Products.DCWorkflow.utils import _dtmldir


class VariableDefinition(SimpleItem):
    """Variable definition"""

    meta_type = 'Workflow Variable'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    description = ''
    for_catalog = 1
    for_status = 1
    default_value = ''
    default_expr = None  # Overrides default_value if set
    info_guard = None
    update_always = 1

    manage_options = (
        {'label': 'Properties', 'action': 'manage_properties'},
        )

    def __init__(self, id):
        self.id = id

    def getDefaultExprText(self):
        if not self.default_expr:
            return ''
        else:
            return self.default_expr.text

    def getInfoGuard(self):
        if self.info_guard is not None:
            return self.info_guard
        else:
            return Guard().__of__(self)  # Create a temporary guard.

    def getInfoGuardSummary(self):
        res = None
        if self.info_guard is not None:
            res = self.info_guard.getSummary()
        return res

    _properties_form = DTMLFile('variable_properties', _dtmldir)

    def manage_properties(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._properties_form(REQUEST,
                                     management_view='Properties',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    def setProperties(self, description,
                      default_value='', default_expr='',
                      for_catalog=0, for_status=0,
                      update_always=0,
                      props=None, REQUEST=None):
        '''
        '''
        self.description = str(description)
        self.default_value = str(default_value)
        if default_expr:
            self.default_expr = Expression(default_expr)
        else:
            self.default_expr = None

        g = Guard()
        if g.changeFromProperties(props or REQUEST):
            self.info_guard = g
        else:
            self.info_guard = None
        self.for_catalog = bool(for_catalog)
        self.for_status = bool(for_status)
        self.update_always = bool(update_always)
        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

InitializeClass(VariableDefinition)


class Variables(ContainerTab):
    """A container for variable definitions"""

    meta_type = 'Workflow Variables'

    all_meta_types = ({'name':VariableDefinition.meta_type,
                       'action':'addVariable',
                       'permission': ManagePortal,
                       },)

    _manage_variables = DTMLFile('variables', _dtmldir)

    def manage_main(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._manage_variables(
            REQUEST,
            management_view='Variables',
            manage_tabs_message=manage_tabs_message,
            )

    def addVariable(self, id, REQUEST=None):
        '''
        '''
        vdef = VariableDefinition(id)
        self._setObject(id, vdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Variable added.')

    def deleteVariables(self, ids, REQUEST=None):
        '''
        '''
        for id in ids:
            self._delObject(id)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Variable(s) removed.')

    def _checkId(self, id, allow_dup=0):
        wf_def = aq_parent(aq_inner(self))
        if id == wf_def.state_var:
            raise BadRequest('"%s" is used for keeping state.' % id)
        return ContainerTab._checkId(self, id, allow_dup)

    def getStateVar(self):
        wf_def = aq_parent(aq_inner(self))
        return wf_def.state_var

    def setStateVar(self, id, REQUEST=None):
        '''
        '''
        wf_def = aq_parent(aq_inner(self))
        if id != wf_def.state_var:
            self._checkId(id)
            wf_def.state_var = str(id)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Set state variable.')

InitializeClass(Variables)
