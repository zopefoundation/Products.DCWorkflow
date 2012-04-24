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
""" States in a web-configurable workflow.
"""

from AccessControl.requestmethod import postonly
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Persistence import PersistentMapping
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.DCWorkflow.ContainerTab import ContainerTab
from Products.DCWorkflow.permissions import ManagePortal
from Products.DCWorkflow.utils import _dtmldir


class StateDefinition(SimpleItem):

    """State definition"""

    meta_type = 'Workflow State'

    manage_options = (
        {'label': 'Properties', 'action': 'manage_properties'},
        {'label': 'Permissions', 'action': 'manage_permissions'},
        {'label': 'Groups', 'action': 'manage_groups'},
        {'label': 'Variables', 'action': 'manage_variables'})

    title = ''
    description = ''
    transitions = ()  # The ids of possible transitions.
    permission_roles = None  # { permission: [role] or (role,) }
    group_roles = None  # { group name : (role,) }
    var_values = None  # PersistentMapping if set.  Overrides transition exprs.

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    def __init__(self, id):
        self.id = id

    def getId(self):
        return self.id

    def getWorkflow(self):
        return aq_parent(aq_inner(aq_parent(aq_inner(self))))

    def getTransitions(self):
        return [ t for t in self.transitions
                 if t in self.getWorkflow().transitions ]

    def getTransitionTitle(self, tid):
        t = self.getWorkflow().transitions.get(tid, None)
        if t is not None:
            return t.title
        return ''

    def getAvailableTransitionIds(self):
        return self.getWorkflow().transitions.keys()

    def getAvailableVarIds(self):
        return self.getWorkflow().variables.keys()

    def getManagedPermissions(self):
        return list(self.getWorkflow().permissions)

    def getAvailableRoles(self):
        return self.getWorkflow().getAvailableRoles()

    def getPermissionInfo(self, p):
        """Returns the list of roles to be assigned to a permission.
        """
        roles = None
        if self.permission_roles:
            roles = self.permission_roles.get(p, None)
        if roles is None:
            return {'acquired': 1, 'roles': []}
        else:
            if isinstance(roles, tuple):
                acq = 0
            else:
                acq = 1
            return {'acquired': acq, 'roles': list(roles)}

    def getGroupInfo(self, group):
        """Returns the list of roles to be assigned to a group.
        """
        if self.group_roles:
            return self.group_roles.get(group, ())
        return ()

    _properties_form = DTMLFile('state_properties', _dtmldir)

    def manage_properties(self, REQUEST, manage_tabs_message=None):
        """Show state properties ZMI form."""
        return self._properties_form(REQUEST,
                                     management_view='Properties',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    def setProperties(self, title='', transitions=(), REQUEST=None,
                      description=''):
        """Set the properties for this State."""
        self.title = str(title)
        self.description = str(description)
        self.transitions = tuple(map(str, transitions))
        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

    _variables_form = DTMLFile('state_variables', _dtmldir)

    def manage_variables(self, REQUEST, manage_tabs_message=None):
        """Show State variables ZMI form."""
        return self._variables_form(REQUEST,
                                     management_view='Variables',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    def getVariableValues(self):
        """Get VariableValues for management UI."""
        vv = self.var_values
        if vv is None:
            return []
        else:
            return vv.items()

    def getWorkflowVariables(self):
        """Get all variables that are available from the workflow and
        not handled yet.
        """
        wf_vars = self.getAvailableVarIds()
        if self.var_values is None:
            return wf_vars
        ret = []
        for vid in wf_vars:
            if not vid in self.var_values:
                ret.append(vid)
        return ret

    def addVariable(self, id, value, REQUEST=None):
        """Add a WorkflowVariable to State."""
        if self.var_values is None:
            self.var_values = PersistentMapping()

        self.var_values[id] = value

        if REQUEST is not None:
            return self.manage_variables(REQUEST, 'Variable added.')

    def deleteVariables(self, ids=[], REQUEST=None):
        """Delete a WorkflowVariable from State."""
        vv = self.var_values
        for id in ids:
            if id in vv:
                del vv[id]

        if REQUEST is not None:
            return self.manage_variables(REQUEST, 'Variables deleted.')

    def setVariables(self, ids=[], REQUEST=None):
        """Set values for Variables set by this State."""
        if self.var_values is None:
            self.var_values = PersistentMapping()

        vv = self.var_values

        if REQUEST is not None:
            for id in vv.keys():
                fname = 'varval_%s' % id
                vv[id] = str(REQUEST[fname])
            return self.manage_variables(REQUEST, 'Variables changed.')

    _permissions_form = DTMLFile('state_permissions', _dtmldir)

    def manage_permissions(self, REQUEST, manage_tabs_message=None):
        """Present TTW UI for managing this State's permissions."""
        return self._permissions_form(REQUEST,
                                     management_view='Permissions',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    @postonly
    def setPermissions(self, REQUEST):
        """Set the permissions in REQUEST for this State."""
        pr = self.permission_roles
        if pr is None:
            self.permission_roles = pr = PersistentMapping()
        pr.clear()
        for p in self.getManagedPermissions():
            roles = []
            acquired = REQUEST.get('acquire_' + p, 0)
            for r in self.getAvailableRoles():
                if REQUEST.get('%s|%s' % (p, r), 0):
                    roles.append(r)
            roles.sort()
            if not acquired:
                roles = tuple(roles)
            pr[p] = roles
        return self.manage_permissions(REQUEST, 'Permissions changed.')

    @postonly
    def setPermission(self, permission, acquired, roles, REQUEST=None):
        """Set a permission for this State."""
        pr = self.permission_roles
        if pr is None:
            self.permission_roles = pr = PersistentMapping()
        if acquired:
            roles = list(roles)
        else:
            roles = tuple(roles)
        pr[permission] = roles

    manage_groups = PageTemplateFile('state_groups.pt', _dtmldir)

    @postonly
    def setGroups(self, REQUEST, RESPONSE=None):
        """Set the group to role mappings in REQUEST for this State.
        """
        map = self.group_roles
        if map is None:
            self.group_roles = map = PersistentMapping()
        map.clear()
        all_roles = self.getWorkflow().getRoles()
        for group in self.getWorkflow().getGroups():
            roles = []
            for role in all_roles:
                if REQUEST.get('%s|%s' % (group, role), 0):
                    roles.append(role)
            roles.sort()
            roles = tuple(roles)
            map[group] = roles
        if RESPONSE is not None:
            RESPONSE.redirect(
                "%s/manage_groups?manage_tabs_message=Groups+changed."
                % self.absolute_url())

InitializeClass(StateDefinition)


class States(ContainerTab):

    """A container for state definitions"""

    meta_type = 'Workflow States'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    all_meta_types = ({'name': StateDefinition.meta_type,
                       'action': 'addState',
                       'permission': ManagePortal},)

    _manage_states = DTMLFile('states', _dtmldir)

    def manage_main(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._manage_states(REQUEST,
                                   management_view='States',
                                   manage_tabs_message=manage_tabs_message,
                                   )

    def addState(self, id, REQUEST=None):
        '''
        '''
        sdef = StateDefinition(id)
        self._setObject(id, sdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'State added.')

    def deleteStates(self, ids, REQUEST=None):
        '''
        '''
        for id in ids:
            self._delObject(id)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'State(s) removed.')

    def setInitialState(self, id=None, ids=None, REQUEST=None):
        '''
        '''
        if not id:
            if len(ids) != 1:
                raise ValueError('One and only one state must be selected')
            id = ids[0]
        id = str(id)
        aq_parent(aq_inner(self)).initial_state = id
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Initial state selected.')

InitializeClass(States)
