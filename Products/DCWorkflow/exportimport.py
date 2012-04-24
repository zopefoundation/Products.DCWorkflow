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
"""DCWorkflow export / import support.
"""

import re
from xml.dom.minidom import parseString

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.class_init import InitializeClass
from Persistence import PersistentMapping
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope.component import adapts

from Products.CMFCore.Expression import Expression
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Guard import Guard
from Products.DCWorkflow.interfaces import IDCWorkflowDefinition
from Products.DCWorkflow.permissions import ManagePortal
from Products.DCWorkflow.utils import _xmldir
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import BodyAdapterBase

TRIGGER_TYPES = ('AUTOMATIC', 'USER')
_FILENAME = 'workflows.xml'


class DCWorkflowDefinitionBodyAdapter(BodyAdapterBase):

    """Body im- and exporter for DCWorkflowDefinition.
    """

    adapts(IDCWorkflowDefinition, ISetupEnviron)

    def _exportBody(self):
        """Export the object as a file body.
        """
        wfdc = WorkflowDefinitionConfigurator(self.context)
        return wfdc.__of__(self.context).generateWorkflowXML()

    def _importBody(self, body):
        """Import the object from the file body.
        """
        encoding = 'utf-8'
        wfdc = WorkflowDefinitionConfigurator(self.context)

        (_workflow_id,
         title,
         state_variable,
         initial_state,
         states,
         transitions,
         variables,
         worklists,
         permissions,
         scripts,
         description,
         manager_bypass,
         creation_guard
        ) = wfdc.parseWorkflowXML(body, encoding)

        _initDCWorkflow(self.context,
                        title,
                        description,
                        manager_bypass,
                        creation_guard,
                        state_variable,
                        initial_state,
                        states,
                        transitions,
                        variables,
                        worklists,
                        permissions,
                        scripts,
                        self.environ)

    body = property(_exportBody, _importBody)

    mime_type = 'text/xml'

    suffix = '/definition.xml'


class WorkflowDefinitionConfigurator(Implicit):
    """ Synthesize XML description of site's workflows.
    """
    security = ClassSecurityInfo()

    def __init__(self, obj):
        self._obj = obj

    security.declareProtected(ManagePortal, 'getWorkflowInfo')
    def getWorkflowInfo(self, workflow_id):
        """ Return a mapping describing a given workflow.

        o Keys in the mappings:

          'id' -- the ID of the workflow within the tool

          'meta_type' -- the workflow's meta_type

          'title' -- the workflow's title property

          'description' -- the workflow's description property

        o See '_extractDCWorkflowInfo' below for keys present only for
          DCWorkflow definitions.

        """
        workflow = self._obj

        workflow_info = {'id': workflow_id,
                         'meta_type': workflow.meta_type,
                         'title': workflow.title_or_id(),
                         'description': workflow.description}

        if workflow.meta_type == DCWorkflowDefinition.meta_type:
            self._extractDCWorkflowInfo(workflow, workflow_info)

        return workflow_info

    security.declareProtected(ManagePortal, 'generateWorkflowXML')
    def generateWorkflowXML(self):
        """ Pseudo API.
        """
        return self._workflowConfig(workflow_id=self._obj.getId())\
            .encode('utf-8')

    security.declareProtected(ManagePortal, 'getWorkflowScripts')
    def getWorkflowScripts(self):
        """ Get workflow scripts information
        """
        return self._extractScripts(self._obj)

    security.declareProtected(ManagePortal, 'parseWorkflowXML')
    def parseWorkflowXML(self, xml, encoding='utf-8'):
        """ Pseudo API.
        """
        dom = parseString(xml)

        root = dom.getElementsByTagName('dc-workflow')[0]

        workflow_id = _getNodeAttribute(root, 'workflow_id', encoding)
        title = _getNodeAttribute(root, 'title', encoding)
        try:
            description = _getNodeAttribute(root, 'description', encoding)
        except ValueError:
            # Don't fail on export files that do not have the description
            # field!
            description = ''
        manager_bypass = _queryNodeAttributeBoolean(root, 'manager_bypass',
                                                    False)
        creation_guard = _extractCreationGuard(root, encoding)
        state_variable = _getNodeAttribute(root, 'state_variable', encoding)
        initial_state = _getNodeAttribute(root, 'initial_state', encoding)

        states = _extractStateNodes(root, encoding)
        transitions = _extractTransitionNodes(root, encoding)
        variables = _extractVariableNodes(root, encoding)
        worklists = _extractWorklistNodes(root, encoding)
        permissions = _extractPermissionNodes(root, encoding)
        scripts = _extractScriptNodes(root, encoding)

        return (workflow_id,
                title,
                state_variable,
                initial_state,
                states,
                transitions,
                variables,
                worklists,
                permissions,
                scripts,
                description,
                manager_bypass,
                creation_guard)

    security.declarePrivate('_workflowConfig')
    _workflowConfig = PageTemplateFile('wtcWorkflowExport.xml', _xmldir,
                                       __name__='workflowConfig')

    security.declarePrivate('_extractDCWorkflowInfo')
    def _extractDCWorkflowInfo(self, workflow, workflow_info):
        """ Append the information for a 'workflow' into 'workflow_info'

        o 'workflow' must be a DCWorkflowDefinition instance.

        o 'workflow_info' must be a dictionary.

        o The following keys will be added to 'workflow_info':

          'creation_guard' -- the guard of 'Instance creation conditions'

          'permissions' -- a list of names of permissions managed
            by the workflow

          'state_variable' -- the name of the workflow's "main"
            state variable

          'initial_state' -- the name of the state in the workflow
            in which objects start their lifecycle.

          'variable_info' -- a list of mappings describing the
            variables tracked by the workflow (see '_extractVariables').

          'state_info' -- a list of mappings describing the
            states tracked by the workflow (see '_extractStates').

          'transition_info' -- a list of mappings describing the
            transitions tracked by the workflow (see '_extractTransitions').

          'worklist_info' -- a list of mappings describing the
            worklists tracked by the workflow (see '_extractWorklists').

          'script_info' -- a list of mappings describing the scripts which
            provide added business logic (see '_extractScripts').
        """
        workflow_info['manager_bypass'] = bool(workflow.manager_bypass)
        workflow_info['creation_guard'] = self._extractCreationGuard(workflow)
        workflow_info['state_variable'] = workflow.state_var
        workflow_info['initial_state'] = workflow.initial_state
        workflow_info['permissions'] = workflow.permissions
        workflow_info['variable_info'] = self._extractVariables(workflow)
        workflow_info['state_info'] = self._extractStates(workflow)
        workflow_info['transition_info'] = self._extractTransitions(workflow)
        workflow_info['worklist_info'] = self._extractWorklists(workflow)
        workflow_info['script_info'] = self._extractScripts(workflow)

    security.declarePrivate('_extractCreationGuard')
    def _extractCreationGuard(self, workflow):
        """ Return a mapping describing 'Instance creation conditions'
            if 'creation_guard' is initialized or None
        """
        guard = workflow.creation_guard
        if guard is not None:
            info = {'guard_permissions': guard.permissions,
                    'guard_roles': guard.roles,
                    'guard_groups': guard.groups,
                    'guard_expr': guard.getExprText()}
            return info

    security.declarePrivate('_extractVariables')
    def _extractVariables(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow variables.

        o Keys for each mapping will include:

          'id' -- the variable's ID

          'description' -- a textual description of the variable

          'for_catalog' -- whether to catalog this variable

          'for_status' -- whether to ??? this variable (XXX)

          'update_always' -- whether to update this variable whenever
            executing a transition (xxX)

          'default_value' -- a default value for the variable (XXX)

          'default_expression' -- a TALES expression for the default value

          'guard_permissions' -- a list of permissions guarding access
            to the variable

          'guard_roles' -- a list of roles guarding access
            to the variable

          'guard_groups' -- a list of groups guarding the transition

          'guard_expr' -- an expression guarding access to the variable
        """
        result = []

        items = workflow.variables.objectItems()
        items.sort()

        for k, v in items:

            guard = v.getInfoGuard()

            default_type = _guessVariableType(v.default_value)

            info = {'id': k,
                    'description': v.description,
                    'for_catalog': bool(v.for_catalog),
                    'for_status': bool(v.for_status),
                    'update_always': bool(v.update_always),
                    'default_value': v.default_value,
                    'default_type': default_type,
                    'default_expr': v.getDefaultExprText(),
                    'guard_permissions': guard.permissions,
                    'guard_roles': guard.roles,
                    'guard_groups': guard.groups,
                    'guard_expr': guard.getExprText()}

            result.append(info)

        return result

    security.declarePrivate('_extractStates')
    def _extractStates(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow states.

        o Within the workflow mapping, each 'state_info' mapping has keys:

          'id' -- the state's ID

          'title' -- the state's title

          'description' -- the state's description

          'transitions' -- a list of IDs of transitions out of the state

          'permissions' -- a list of mappings describing the permission
            map for the state

          'groups' -- a list of ( group_id, (roles,) ) tuples describing the
            group-role assignments for the state

          'variables' -- a list of mapping for the variables
            to be set when entering the state.

        o Within the state_info mappings, each 'permissions' mapping
          has the keys:

          'name' -- the name of the permission

          'roles' -- a sequence of role IDs which have the permission

          'acquired' -- whether roles are acquired for the permission

        o Within the state_info mappings, each 'variable' mapping
          has the keys:

          'name' -- the name of the variable

          'type' -- the type of the value (allowed values are:
                    'string', 'datetime', 'bool', 'int')

          'value' -- the value to be set
        """
        result = []

        items = workflow.states.objectItems()
        items.sort()

        for k, v in items:

            groups = v.group_roles and list(v.group_roles.items()) or []
            groups = [ x for x in groups if x[1] ]
            groups.sort()

            variables = list(v.getVariableValues())
            variables.sort()

            v_info = []

            for v_name, value in variables:
                v_info.append({'name': v_name,
                               'type': _guessVariableType(value),
                               'value': value})

            info = {'id': k,
                    'title': v.title,
                    'description': v.description,
                    'transitions': v.transitions,
                    'permissions': self._extractStatePermissions(v),
                    'groups': groups,
                    'variables': v_info}

            result.append(info)

        return result

    security.declarePrivate('_extractStatePermissions')
    def _extractStatePermissions(self, state):
        """ Return a sequence of mappings for the permissions in a state.

        o Each mapping has the keys:

          'name' -- the name of the permission

          'roles' -- a sequence of role IDs which have the permission

          'acquired' -- whether roles are acquired for the permission
        """
        result = []
        perm_roles = state.permission_roles

        if perm_roles:
            items = state.permission_roles.items()
            items.sort()

            for k, v in items:
                result.append({'name': k,
                               'roles': v,
                               'acquired': not isinstance(v, tuple)})

        return result

    security.declarePrivate('_extractTransitions')
    def _extractTransitions(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow transitions.

        o Each mapping has the keys:

          'id' -- the transition's ID

          'title' -- the transition's ID

          'description' -- the transition's description

          'new_state_id' -- the ID of the state into which the transition
            moves an object

          'trigger_type' -- one of the following values, indicating how the
            transition is fired:

            - "AUTOMATIC" -> fired opportunistically whenever the workflow
               notices that its guard conditions permit

            - "USER" -> fired in response to user request

          'script_name' -- the ID of a script to be executed before
             the transition

          'after_script_name' -- the ID of a script to be executed after
             the transition

          'actbox_name' -- the name of the action by which the user
             triggers the transition

          'actbox_url' -- the URL of the action by which the user
             triggers the transition

          'actbox_icon' -- the icon URL for the action by which the user
             triggers the transition

          'actbox_category' -- the category of the action by which the user
             triggers the transition

          'variables' -- a list of ( id, expr ) tuples defining how variables
            are to be set during the transition

          'guard_permissions' -- a list of permissions guarding the transition

          'guard_roles' -- a list of roles guarding the transition

          'guard_groups' -- a list of groups guarding the transition

          'guard_expr' -- an expression guarding the transition

        """
        result = []

        items = workflow.transitions.objectItems()
        items.sort()

        for k, v in items:

            guard = v.getGuard()

            v_info = []

            for v_name, expr in v.getVariableExprs():
                v_info.append({'name': v_name, 'expr': expr})

            info = {'id': k,
                    'title': v.title,
                    'description': v.description,
                    'new_state_id': v.new_state_id,
                    'trigger_type': TRIGGER_TYPES[v.trigger_type],
                    'script_name': v.script_name,
                    'after_script_name': v.after_script_name,
                    'actbox_name': v.actbox_name,
                    'actbox_url': v.actbox_url,
                    'actbox_icon': v.actbox_icon,
                    'actbox_category': v.actbox_category,
                    'variables': v_info,
                    'guard_permissions': guard.permissions,
                    'guard_roles': guard.roles,
                    'guard_groups': guard.groups,
                    'guard_expr': guard.getExprText()}

            result.append(info)

        return result

    security.declarePrivate('_extractWorklists')
    def _extractWorklists(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow transitions.

        o Each mapping has the keys:

          'id' -- the ID of the worklist

          'title' -- the title of the worklist

          'description' -- a textual description of the worklist

          'var_match' -- a list of ( key, value ) tuples defining
            the variables used to "activate" the worklist.

          'actbox_name' -- the name of the "action" corresponding to the
            worklist

          'actbox_url' -- the URL of the "action" corresponding to the
            worklist

          'actbox_icon' -- the icon URL of the "action" corresponding to
            the worklist

          'actbox_category' -- the category of the "action" corresponding
            to the worklist

          'guard_permissions' -- a list of permissions guarding access
            to the worklist

          'guard_roles' -- a list of roles guarding access
            to the worklist

          'guard_expr' -- an expression guarding access to the worklist

        """
        result = []

        items = workflow.worklists.objectItems()
        items.sort()

        for k, v in items:

            guard = v.getGuard()

            var_match = [ (id, v.getVarMatchText(id))
                          for id in v.getVarMatchKeys() ]

            info = {'id': k,
                    'title': v.title,
                    'description': v.description,
                    'var_match': var_match,
                    'actbox_name': v.actbox_name,
                    'actbox_url': v.actbox_url,
                    'actbox_icon': v.actbox_icon,
                    'actbox_category': v.actbox_category,
                    'guard_permissions': guard.permissions,
                    'guard_roles': guard.roles,
                    'guard_groups': guard.groups,
                    'guard_expr': guard.getExprText()}

            result.append(info)

        return result

    security.declarePrivate('_extractScripts')
    def _extractScripts(self, workflow):
        """ Return a sequence of mappings describing DCWorkflow scripts.

        o Each mapping has the keys:

          'id' -- the ID of the script

          'meta_type' -- the title of the worklist

          'body' -- the text of the script (only applicable to scripts
            of type Script (Python))

          'module' -- The module from where to load the function (only
            applicable to External Method scripts)

          'function' -- The function to load from the 'module' given
            (Only applicable to External Method scripts)

          'filename' -- the name of the file to / from which the script
            is stored / loaded (Script (Python) only)
        """
        result = []

        items = workflow.scripts.objectItems()
        items.sort()

        for k, v in items:

            filename = _getScriptFilename(workflow.getId(), k, v.meta_type)
            module = ''
            function = ''

            if v.meta_type == 'External Method':
                module = v.module()
                function = v.function()

            info = {'id': k,
                    'meta_type': v.meta_type,
                    'module': module,
                    'function': function,
                    'filename': filename}

            result.append(info)

        return result

InitializeClass(WorkflowDefinitionConfigurator)


def _getScriptFilename(workflow_id, script_id, meta_type):
    """ Return the name of the file which holds the script.
    """
    wf_dir = workflow_id.replace(' ', '_')
    suffix = _METATYPE_SUFFIXES.get(meta_type, None)

    if suffix is None:
        return ''

    return 'workflows/%s/scripts/%s.%s' % (wf_dir, script_id, suffix)

def _extractCreationGuard(root, encoding='utf-8'):
    icc = root.getElementsByTagName('instance-creation-conditions')
    assert len(icc) <= 1
    if icc:
        parent = icc[0]
        return _extractGuardNode(parent, encoding)
    else:
        return None

def _extractStateNodes(root, encoding='utf-8'):
    result = []

    for s_node in root.getElementsByTagName('state'):
        info = {'state_id': _getNodeAttribute(s_node, 'state_id', encoding),
                'title': _getNodeAttribute(s_node, 'title', encoding),
                'description': _extractDescriptionNode(s_node, encoding)}

        info['transitions'] = [ _getNodeAttribute(x, 'transition_id', encoding)
                                for x in s_node.getElementsByTagName(
                                                           'exit-transition') ]

        info['permissions'] = permission_map = {}

        for p_map in s_node.getElementsByTagName('permission-map'):

            name = _getNodeAttribute(p_map, 'name', encoding)
            acquired = _queryNodeAttributeBoolean(p_map, 'acquired', False)

            roles = [ _coalesceTextNodeChildren(x, encoding)
                      for x in p_map.getElementsByTagName('permission-role') ]

            if not acquired:
                roles = tuple(roles)

            permission_map[name] = roles

        info['groups'] = group_map = []

        for g_map in s_node.getElementsByTagName('group-map'):

            name = _getNodeAttribute(g_map, 'name', encoding)

            roles = [ _coalesceTextNodeChildren(x, encoding)
                      for x in g_map.getElementsByTagName('group-role') ]

            group_map.append((name, tuple(roles)))

        info['variables'] = var_map = {}

        for assignment in s_node.getElementsByTagName('assignment'):

            name = _getNodeAttribute(assignment, 'name', encoding)
            type_id = _getNodeAttribute(assignment, 'type', encoding)
            value = _coalesceTextNodeChildren(assignment, encoding)

            var_map[name] = {'name': name, 'type': type_id, 'value': value}

        result.append(info)

    return result

def _extractTransitionNodes(root, encoding='utf-8'):
    result = []

    for t_node in root.getElementsByTagName('transition'):

        info = {'transition_id': _getNodeAttribute(t_node, 'transition_id',
                                                   encoding),
                'title': _getNodeAttribute(t_node, 'title', encoding),
                'description': _extractDescriptionNode(t_node, encoding),
                'new_state': _getNodeAttribute(t_node, 'new_state', encoding),
                'trigger': _getNodeAttribute(t_node, 'trigger', encoding),
                'before_script': _getNodeAttribute(t_node, 'before_script',
                                                   encoding),
                'after_script': _getNodeAttribute(t_node, 'after_script',
                                                  encoding),
                'action': _extractActionNode(t_node, encoding),
                'guard': _extractGuardNode(t_node, encoding)}

        info['variables'] = var_map = {}

        for assignment in t_node.getElementsByTagName('assignment'):

            name = _getNodeAttribute(assignment, 'name', encoding)
            expr = _coalesceTextNodeChildren(assignment, encoding)
            var_map[name] = expr

        result.append(info)

    return result

def _extractVariableNodes(root, encoding='utf-8'):
    result = []

    for v_node in root.getElementsByTagName('variable'):

        info = {'variable_id': _getNodeAttribute(v_node, 'variable_id',
                                                 encoding),
                'description': _extractDescriptionNode(v_node, encoding),
                'for_catalog': _queryNodeAttributeBoolean(v_node,
                                                         'for_catalog', False),
                'for_status': _queryNodeAttributeBoolean(v_node, 'for_status',
                                                         False),
                'update_always': _queryNodeAttributeBoolean(v_node,
                                                       'update_always', False),
                'default': _extractDefaultNode(v_node, encoding),
                'guard': _extractGuardNode(v_node, encoding)}

        result.append(info)

    return result

def _extractWorklistNodes(root, encoding='utf-8'):
    result = []

    for w_node in root.getElementsByTagName('worklist'):

        info = {'worklist_id': _getNodeAttribute(w_node, 'worklist_id',
                                                 encoding),
                'title': _getNodeAttribute(w_node, 'title', encoding),
                'description': _extractDescriptionNode(w_node, encoding),
                'match': _extractMatchNode(w_node, encoding),
                'action': _extractActionNode(w_node, encoding),
                'guard': _extractGuardNode(w_node, encoding)}

        result.append(info)

    return result

def _extractScriptNodes(root, encoding='utf-8'):
    result = []

    for s_node in root.getElementsByTagName('script'):

        try:
            function = _getNodeAttribute(s_node, 'function')
        except ValueError:
            function = ''

        try:
            module = _getNodeAttribute(s_node, 'module')
        except ValueError:
            module = ''

        info = {'script_id': _getNodeAttribute(s_node, 'script_id'),
                'meta_type': _getNodeAttribute(s_node, 'type', encoding),
                'function': function,
                'module': module}

        filename = _queryNodeAttribute(s_node, 'filename', None, encoding)

        if filename is not None:
            info['filename'] = filename

        result.append(info)

    return result

def _extractPermissionNodes(root, encoding='utf-8'):
    result = []

    for p_node in root.getElementsByTagName('permission'):

        result.append(_coalesceTextNodeChildren(p_node, encoding))

    return result

def _extractActionNode(parent, encoding='utf-8'):
    nodes = parent.getElementsByTagName('action')
    assert len(nodes) <= 1, nodes

    if len(nodes) < 1:
        return {'name': '', 'url': '', 'category': '', 'icon': ''}

    node = nodes[0]

    return {'name': _coalesceTextNodeChildren(node, encoding),
            'url': _getNodeAttribute(node, 'url', encoding),
            'category': _getNodeAttribute(node, 'category', encoding),
            'icon': _queryNodeAttribute(node, 'icon', '', encoding)}

def _extractGuardNode(parent, encoding='utf-8'):
    nodes = parent.getElementsByTagName('guard')
    assert len(nodes) <= 1, nodes

    if len(nodes) < 1:
        return {'permissions': (), 'roles': (), 'groups': (), 'expr': ''}

    node = nodes[0]

    expr_nodes = node.getElementsByTagName('guard-expression')
    assert(len(expr_nodes) <= 1)

    expr_text = expr_nodes and _coalesceTextNodeChildren(expr_nodes[0],
                                                         encoding) or ''

    return {'permissions': [ _coalesceTextNodeChildren(x, encoding)
                             for x in node.getElementsByTagName(
                                                         'guard-permission') ],
            'roles': [ _coalesceTextNodeChildren(x, encoding)
                       for x in node.getElementsByTagName('guard-role') ],
            'groups': [ _coalesceTextNodeChildren(x, encoding)
                        for x in node.getElementsByTagName('guard-group') ],
            'expression': expr_text}

def _extractDefaultNode(parent, encoding='utf-8'):
    nodes = parent.getElementsByTagName('default')
    assert len(nodes) <= 1, nodes

    if len(nodes) < 1:
        return {'value': '', 'expression': '', 'type': 'n/a'}

    node = nodes[0]

    value_nodes = node.getElementsByTagName('value')
    assert(len(value_nodes) <= 1)

    value_type = 'n/a'
    if value_nodes:
        value_type = value_nodes[0].getAttribute('type') or 'n/a'

    value_text = value_nodes and _coalesceTextNodeChildren(value_nodes[0],
                                                           encoding) or ''

    expr_nodes = node.getElementsByTagName('expression')
    assert(len(expr_nodes) <= 1)

    expr_text = expr_nodes and _coalesceTextNodeChildren(expr_nodes[0],
                                                         encoding) or ''

    return {'value': value_text, 'type': value_type, 'expression': expr_text}

_SEMICOLON_LIST_SPLITTER = re.compile(r';[ ]*')

def _extractMatchNode(parent, encoding='utf-8'):
    nodes = parent.getElementsByTagName('match')

    result = {}

    for node in nodes:

        name = _getNodeAttribute(node, 'name', encoding)
        values = _getNodeAttribute(node, 'values', encoding)
        result[name] = _SEMICOLON_LIST_SPLITTER.split(values)

    return result

def _guessVariableType(value):
    from DateTime.DateTime import DateTime

    if value is None:
        return 'none'

    if isinstance(value, DateTime):
        return 'datetime'

    if isinstance(value, bool):
        return 'bool'

    if isinstance(value, int):
        return 'int'

    if isinstance(value, float):
        return 'float'

    if isinstance(value, basestring):
        return 'string'

    return 'unknown'

def _convertVariableValue(value, type_id):
    from DateTime.DateTime import DateTime

    if type_id == 'none':
        return None

    if type_id == 'datetime':

        return DateTime(value)

    if type_id == 'bool':

        if isinstance(value, basestring):

            value = str(value).lower()

            return value in ('true', 'yes', '1')

        else:
            return bool(value)

    if type_id == 'int':
        return int(value)

    if type_id == 'float':
        return float(value)

    return value

from Products.PythonScripts.PythonScript import PythonScript
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from OFS.DTMLMethod import DTMLMethod

_METATYPE_SUFFIXES = {
    PythonScript.meta_type: 'py',
    DTMLMethod.meta_type: 'dtml'}

def _initDCWorkflow(workflow,
                    title,
                    description,
                    manager_bypass,
                    creation_guard,
                    state_variable,
                    initial_state,
                    states,
                    transitions,
                    variables,
                    worklists,
                    permissions,
                    scripts,
                    context):
    """ Initialize a DC Workflow using values parsed from XML.
    """
    workflow.title = title
    workflow.description = description
    workflow.manager_bypass = manager_bypass and 1 or 0
    workflow.state_var = state_variable
    workflow.initial_state = initial_state

    permissions = permissions[:]
    permissions.sort()
    workflow.permissions = tuple(permissions)

    _initDCWorkflowCreationGuard(workflow, creation_guard)
    _initDCWorkflowVariables(workflow, variables)
    _initDCWorkflowStates(workflow, states)
    _initDCWorkflowTransitions(workflow, transitions)
    _initDCWorkflowWorklists(workflow, worklists)
    _initDCWorkflowScripts(workflow, scripts, context)


def _initDCWorkflowCreationGuard(workflow, guard):
    """Initialize Instance creation conditions guard
    """
    if guard is None:
        workflow.creation_guard = None
    else:
        props = {'guard_roles': ';'.join(guard['roles']),
                 'guard_permissions': ';'.join(guard['permissions']),
                 'guard_groups': ';'.join(guard['groups']),
                 'guard_expr': guard['expression']}
        g = Guard()
        g.changeFromProperties(props)
        workflow.creation_guard = g

def _initDCWorkflowVariables(workflow, variables):
    """ Initialize DCWorkflow variables
    """
    from Products.DCWorkflow.Variables import VariableDefinition

    for v_info in variables:

        id = str(v_info['variable_id']) # no unicode!
        if not id in workflow.variables:
            v = VariableDefinition(id)
            workflow.variables._setObject(id, v)
        v = workflow.variables._getOb(id)

        guard = v_info['guard']
        props = {'guard_roles': ';'.join(guard['roles']),
                 'guard_permissions': ';'.join(guard['permissions']),
                 'guard_groups': ';'.join(guard['groups']),
                 'guard_expr': guard['expression']}

        default = v_info['default']
        default_value = _convertVariableValue(default['value'],
                                              default['type'])

        v.setProperties(description=v_info['description'],
                        default_value=default_value,
                        default_expr=default['expression'],
                        for_catalog=v_info['for_catalog'],
                        for_status=v_info['for_status'],
                        update_always=v_info['update_always'],
                        props=props)

def _initDCWorkflowStates(workflow, states):
    """ Initialize DCWorkflow states
    """
    from Products.DCWorkflow.States import StateDefinition

    for s_info in states:

        id = str(s_info['state_id']) # no unicode!
        if not id in workflow.states:
            s = StateDefinition(id)
            workflow.states._setObject(id, s)
        s = workflow.states._getOb(id)

        s.setProperties(title=s_info['title'],
                        description=s_info['description'],
                        transitions=s_info['transitions'])

        for k, v in s_info['permissions'].items():
            s.setPermission(k, isinstance(v, list), v)

        gmap = s.group_roles = PersistentMapping()

        for group_id, roles in s_info['groups']:
            gmap[group_id] = roles

        vmap = s.var_values = PersistentMapping()

        for name, v_info in s_info['variables'].items():
            value = _convertVariableValue(v_info['value'], v_info['type'])
            vmap[name] = value

def _initDCWorkflowTransitions(workflow, transitions):
    """ Initialize DCWorkflow transitions
    """
    from Products.DCWorkflow.Transitions import TransitionDefinition

    for t_info in transitions:

        id = str(t_info['transition_id']) # no unicode!
        if not id in workflow.transitions:
            t = TransitionDefinition(id)
            workflow.transitions._setObject(id, t)
        t = workflow.transitions._getOb(id)

        trigger_type = list(TRIGGER_TYPES).index(t_info['trigger'])

        action = t_info['action']

        guard = t_info['guard']
        props = {'guard_roles': ';'.join(guard['roles']),
                 'guard_permissions': ';'.join(guard['permissions']),
                 'guard_groups': ';'.join(guard['groups']),
                 'guard_expr': guard['expression']}

        t.setProperties(title=t_info['title'],
                        description=t_info['description'],
                        new_state_id=t_info['new_state'],
                        trigger_type=trigger_type,
                        script_name=t_info['before_script'],
                        after_script_name=t_info['after_script'],
                        actbox_name=action['name'],
                        actbox_url=action['url'],
                        actbox_category=action['category'],
                        actbox_icon=action.get('icon', ''),
                        props=props)
        var_mapping = [ (name, Expression(text))
                        for name, text in t_info['variables'].items() ]
        t.var_exprs = PersistentMapping(var_mapping)

def _initDCWorkflowWorklists(workflow, worklists):
    """ Initialize DCWorkflow worklists
    """
    from Products.DCWorkflow.Worklists import WorklistDefinition

    for w_info in worklists:

        id = str(w_info['worklist_id']) # no unicode!
        if not id in workflow.worklists:
            w = WorklistDefinition(id)
            workflow.worklists._setObject(id, w)
        w = workflow.worklists._getOb(id)

        action = w_info['action']

        guard = w_info['guard']
        props = {'guard_roles': ';'.join(guard['roles']),
                 'guard_permissions': ';'.join(guard['permissions']),
                 'guard_groups': ';'.join(guard['groups']),
                 'guard_expr': guard['expression']}

        w.setProperties(description=w_info['description'],
                        actbox_name=action['name'],
                        actbox_url=action['url'],
                        actbox_category=action['category'],
                        actbox_icon=action.get('icon', ''),
                        props=props)

        w.var_matches = PersistentMapping()
        for k, v in w_info['match'].items():
            w.var_matches[str(k)] = tuple([ str(x) for x in v ])

def _initDCWorkflowScripts(workflow, scripts, context):
    """ Initialize DCWorkflow scripts
    """
    for s_info in scripts:

        id = str(s_info['script_id']) # no unicode!
        meta_type = s_info['meta_type']
        filename = s_info['filename']
        file = ''

        if filename:
            file = context.readDataFile(filename)

        if meta_type == PythonScript.meta_type:
            script = PythonScript(id)
            script.write(file)

        elif meta_type == ExternalMethod.meta_type:
            script = ExternalMethod(id, '', s_info['module'],
                                    s_info['function'])

        elif meta_type == DTMLMethod.meta_type:
            script = DTMLMethod(file, __name__=id)

        else:
            for mt in workflow.scripts.filtered_meta_types():
                if mt['name'] == meta_type:
                    if hasattr(mt['instance'], 'write'):
                        script = mt['instance'](id)
                        script.write(file)
                    else:
                        script = mt['instance'](file, __name__=id)
                    break
            else:
                raise ValueError('Invalid type: %s' % meta_type)

        if id in workflow.scripts:
            workflow.scripts._delObject(id)
        workflow.scripts._setObject(id, script)

#
#   deprecated DOM parsing utilities
#
_marker = object()

def _queryNodeAttribute(node, attr_name, default, encoding='utf-8'):
    """ Extract a string-valued attribute from node.

    o Return 'default' if the attribute is not present.
    """
    attr_node = node.attributes.get(attr_name, _marker)

    if attr_node is _marker:
        return default

    value = attr_node.nodeValue

    if encoding is not None:
        value = value.encode(encoding)

    return value

def _getNodeAttribute(node, attr_name, encoding='utf-8'):
    """ Extract a string-valued attribute from node.
    """
    value = _queryNodeAttribute(node, attr_name, _marker, encoding)

    if value is _marker:
        raise ValueError('Invalid attribute: %s' % attr_name)

    return value

def _queryNodeAttributeBoolean(node, attr_name, default):
    """ Extract a string-valued attribute from node.

    o Return 'default' if the attribute is not present.
    """
    attr_node = node.attributes.get(attr_name, _marker)

    if attr_node is _marker:
        return default

    value = node.attributes[attr_name].nodeValue.lower()

    return value in ('true', 'yes', '1')

def _getNodeAttributeBoolean(node, attr_name):
    """ Extract a string-valued attribute from node.
    """
    value = node.attributes[attr_name].nodeValue.lower()

    return value in ('true', 'yes', '1')

def _coalesceTextNodeChildren(node, encoding='utf-8'):
    """ Concatenate all childe text nodes into a single string.
    """
    from xml.dom import Node
    fragments = []
    node.normalize()
    child = node.firstChild

    while child is not None:

        if child.nodeType == Node.TEXT_NODE:
            fragments.append(child.nodeValue)

        child = child.nextSibling

    joined = ''.join(fragments)

    if encoding is not None:
        joined = joined.encode(encoding)

    return ''.join([ line.lstrip()
                     for line in joined.splitlines(True) ]).rstrip()

def _extractDescriptionNode(parent, encoding='utf-8'):
    d_nodes = parent.getElementsByTagName('description')
    if d_nodes:
        return _coalesceTextNodeChildren(d_nodes[0], encoding)
    else:
        return ''
