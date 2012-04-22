##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""DCWorkflow export / import unit tests.
"""

import unittest
import Testing

from Products.PythonScripts.PythonScript import PythonScript
from Products.ExternalMethod.ExternalMethod import ExternalMethod

from Products.CMFCore.exportimport.tests.test_workflow \
        import _BINDINGS_TOOL_EXPORT
from Products.CMFCore.exportimport.tests.test_workflow \
        import _EMPTY_TOOL_EXPORT
from Products.CMFCore.exportimport.tests.test_workflow \
        import _WorkflowSetup as WorkflowSetupBase
from Products.CMFCore.testing import DummyWorkflow
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Guard import Guard
from Products.DCWorkflow.testing import ExportImportZCMLLayer
from Products.DCWorkflow.Transitions import TRIGGER_USER_ACTION
from Products.DCWorkflow.Transitions import TRIGGER_AUTOMATIC
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext


class _GuardChecker:

    def _genGuardProps(self, permissions, roles, groups, expr):

        return {'guard_permissions': '; '.join(permissions),
                'guard_roles': '; '.join(roles),
                'guard_groups': '; '.join(groups),
                'guard_expr': expr}

    def _assertGuard(self, info, permissions, roles, groups, expr):

        self.assertEqual(len(info['guard_permissions']), len(permissions))

        for expected in permissions:
            self.assertTrue(expected in info['guard_permissions'])

        self.assertEqual(len(info['guard_roles']), len(roles))

        for expected in roles:
            self.assertTrue(expected in info['guard_roles'])

        self.assertEqual(len(info['guard_groups']), len(groups))

        for expected in groups:
            self.assertTrue(expected in info['guard_groups'])

        self.assertEqual(info['guard_expr'], expr)


class _WorkflowSetup(WorkflowSetupBase):

    def _initDCWorkflow(self, wtool, workflow_id):
        wtool._setObject(workflow_id, DCWorkflowDefinition(workflow_id))

        return wtool._getOb(workflow_id)

    def _initVariables(self, dcworkflow):
        for id, args in _WF_VARIABLES.items():
            dcworkflow.variables.addVariable(id)
            variable = dcworkflow.variables._getOb(id)

            (_descr, _def_val, _def_exp, _for_cat, _for_stat, _upd_alw
            ) = args[:-4]

            variable.setProperties(description=args[0],
                                   default_value=args[1],
                                   default_expr=args[2],
                                   for_catalog=args[3],
                                   for_status=args[4],
                                   update_always=args[5],
                                   props=self._genGuardProps(*args[-4:]))

    def _initStates(self, dcworkflow):
        dcworkflow.groups = _WF_GROUPS

        for k, v in _WF_STATES.items():

            dcworkflow.states.addState(k)
            state = dcworkflow.states._getOb(k)

            state.setProperties(title=v[0],
                                description=v[1],
                                transitions=v[2])
            if not v[3]:
                state.permission_roles = None

            for permission, roles in v[3].items():
                state.setPermission(permission, not isinstance(roles, tuple),
                                    roles)
            faux_request = {}

            for group_id, roles in v[4]:
                for role in roles:
                    faux_request['%s|%s' % (group_id, role)] = True

            state.setGroups(REQUEST=faux_request)

            for k, v in v[5].items():
                state.addVariable(k, v)

    def _initTransitions(self, dcworkflow):
        for k, v in _WF_TRANSITIONS.items():

            dcworkflow.transitions.addTransition(k)
            transition = dcworkflow.transitions._getOb(k)

            transition.setProperties(title=v[0],
                                     description=v[1],
                                     new_state_id=v[2],
                                     trigger_type=v[3],
                                     script_name=v[4],
                                     after_script_name=v[5],
                                     actbox_name=v[6],
                                     actbox_url=v[7],
                                     actbox_icon=v[8],
                                     actbox_category=v[9],
                                     props=self._genGuardProps(*v[-4:]))

            for k, v in v[10].items():
                transition.addVariable(k, v)

    def _initWorklists(self, dcworkflow):

        for k, v in _WF_WORKLISTS.items():

            dcworkflow.worklists.addWorklist(k)
            worklist = dcworkflow.worklists._getOb(k)

            worklist.title = v[0]

            props = self._genGuardProps(*v[-4:])

            for var_id, matches in v[2].items():
                props['var_match_%s' % var_id] = ';'.join(matches)

            worklist.setProperties(description=v[1],
                                   actbox_name=v[3],
                                   actbox_url=v[4],
                                   actbox_icon=v[5],
                                   actbox_category=v[6],
                                   props=props)

    def _initScripts(self, dcworkflow):
        for k, v in _WF_SCRIPTS.items():

            if v[0] == PythonScript.meta_type:
                script = PythonScript(k)
                script.write(v[1])

            elif v[0] == ExternalMethod.meta_type:
                script = ExternalMethod(k, '', v[3], v[4])

            else:
                raise ValueError('Unknown script type: %s' % v[0])

            dcworkflow.scripts._setObject(k, script)

    def _initCreationGuard(self, dcworkflow):
        props = self._genGuardProps(*_CREATION_GUARD)
        g = Guard()
        g.changeFromProperties(props)
        dcworkflow.creation_guard = g


class WorkflowDefinitionConfiguratorTests(_WorkflowSetup, _GuardChecker):

    layer = ExportImportZCMLLayer

    def _getTargetClass(self):
        from Products.DCWorkflow.exportimport \
                import WorkflowDefinitionConfigurator

        return WorkflowDefinitionConfigurator

    def test_getWorkflowInfo_dcworkflow_defaults(self):
        WF_ID = 'dcworkflow_defaults'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        self.assertEqual(info['id'], WF_ID)
        self.assertEqual(info['meta_type'], DCWorkflowDefinition.meta_type)
        self.assertEqual(info['title'], dcworkflow.title)
        self.assertEqual(info['description'], dcworkflow.description)

        self.assertEqual(info['state_variable'], dcworkflow.state_var)

        self.assertEqual(len(info['permissions']), 0)
        self.assertEqual(len(info['variable_info']), 0)
        self.assertEqual(len(info['state_info']), 0)
        self.assertEqual(len(info['transition_info']), 0)

    def test_getWorkflowInfo_dcworkflow_permissions(self):
        WF_ID = 'dcworkflow_permissions'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        dcworkflow.permissions = _WF_PERMISSIONS

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        permissions = info['permissions']
        self.assertEqual(len(permissions), len(_WF_PERMISSIONS))

        for permission in _WF_PERMISSIONS:
            self.assertTrue(permission in permissions)

    def test_getWorkflowInfo_dcworkflow_variables(self):
        WF_ID = 'dcworkflow_variables'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        self._initVariables(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        variable_info = info['variable_info']
        self.assertEqual(len(variable_info), len(_WF_VARIABLES))

        ids = [ x['id'] for x in variable_info ]

        for k in _WF_VARIABLES.keys():
            self.assertTrue(k in ids)

        for info in variable_info:

            expected = _WF_VARIABLES[info['id']]

            self.assertEqual(info['description'], expected[0])
            self.assertEqual(info['default_value'], expected[1])
            self.assertEqual(info['default_expr'], expected[2])
            self.assertEqual(info['for_catalog'], expected[3])
            self.assertEqual(info['for_status'], expected[4])
            self.assertEqual(info['update_always'], expected[5])

            self._assertGuard(info, *expected[-4:])

    def test_getWorkflowInfo_dcworkflow_states(self):
        WF_ID = 'dcworkflow_states'
        WF_INITIAL_STATE = 'closed'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        dcworkflow.initial_state = WF_INITIAL_STATE
        self._initStates(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        self.assertEqual(info['state_variable'], dcworkflow.state_var)
        self.assertEqual(info['initial_state'], dcworkflow.initial_state)

        state_info = info['state_info']
        self.assertEqual(len(state_info), len(_WF_STATES))

        ids = [ x['id'] for x in state_info ]

        for k in _WF_STATES.keys():
            self.assertTrue(k in ids)

        for info in state_info:

            expected = _WF_STATES[info['id']]

            self.assertEqual(info['title'], expected[0])
            self.assertEqual(info['description'], expected[1])
            self.assertEqual(info['transitions'], expected[2])

            permissions = info['permissions']

            self.assertEqual(len(permissions), len(expected[3]))

            for ep_id, ep_roles in expected[3].items():

                fp = [ x for x in permissions if x['name'] == ep_id ][0]

                self.assertEqual(fp['acquired'],
                                 not isinstance(ep_roles, tuple))

                self.assertEqual(len(fp['roles']), len(ep_roles))

                for ep_role in ep_roles:
                    self.assertTrue(ep_role in fp['roles'])

            groups = info['groups']
            self.assertEqual(len(groups), len(expected[4]))

            for i in range(len(groups)):
                self.assertEqual(groups[i], expected[4][i])

            variables = info['variables']
            self.assertEqual(len(variables), len(expected[5]))

            for v_info in variables:

                name, type, value = (v_info['name'], v_info['type'],
                                     v_info['value'])

                self.assertEqual(value, expected[5][name])

                if isinstance(value, bool):
                    self.assertEqual(type, 'bool')
                elif isinstance(value, int):
                    self.assertEqual(type, 'int')
                elif isinstance(value, float):
                    self.assertEqual(type, 'float')
                elif isinstance(value, basestring):
                    self.assertEqual(type, 'string')

    def test_getWorkflowInfo_dcworkflow_transitions(self):
        from Products.DCWorkflow.exportimport import TRIGGER_TYPES

        WF_ID = 'dcworkflow_transitions'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        self._initTransitions(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        transition_info = info['transition_info']
        self.assertEqual(len(transition_info), len(_WF_TRANSITIONS))

        ids = [ x['id'] for x in transition_info ]

        for k in _WF_TRANSITIONS.keys():
            self.assertTrue(k in ids)

        for info in transition_info:

            expected = _WF_TRANSITIONS[info['id']]

            self.assertEqual(info['title'], expected[0])
            self.assertEqual(info['description'], expected[1])
            self.assertEqual(info['new_state_id'], expected[2])
            self.assertEqual(info['trigger_type'], TRIGGER_TYPES[expected[3]])
            self.assertEqual(info['script_name'], expected[4])
            self.assertEqual(info['after_script_name'], expected[5])
            self.assertEqual(info['actbox_name'], expected[6])
            self.assertEqual(info['actbox_url'], expected[7])
            self.assertEqual(info['actbox_icon'], expected[8])
            self.assertEqual(info['actbox_category'], expected[9])

            variables = info['variables']
            self.assertEqual(len(variables), len(expected[10]))

            for v_info in variables:
                self.assertEqual(v_info['expr'], expected[10][v_info['name']])

            self._assertGuard(info, *expected[-4:])

    def test_getWorkflowInfo_dcworkflow_worklists(self):
        WF_ID = 'dcworkflow_worklists'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        self._initWorklists(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        worklist_info = info['worklist_info']
        self.assertEqual(len(worklist_info), len(_WF_WORKLISTS))

        ids = [ x['id'] for x in worklist_info ]

        for k in _WF_WORKLISTS.keys():
            self.assertTrue(k in ids)

        for info in worklist_info:

            expected = _WF_WORKLISTS[info['id']]

            self.assertEqual(info['title'], expected[0])
            self.assertEqual(info['description'], expected[1])
            self.assertEqual(info['actbox_name'], expected[3])
            self.assertEqual(info['actbox_url'], expected[4])
            self.assertEqual(info['actbox_icon'], expected[5])
            self.assertEqual(info['actbox_category'], expected[6])

            var_match = info['var_match']
            self.assertEqual(len(var_match), len(expected[2]))

            for var_id, values_txt in var_match:

                values = [ x.strip() for x in values_txt.split(';') ]
                e_values = expected[2][var_id]
                self.assertEqual(len(values), len(e_values))

                for e_value in e_values:
                    self.assertTrue(e_value in values)

            self._assertGuard(info, *expected[-4:])

    def test_getWorkflowInfo_dcworkflow_scripts(self):
        WF_ID = 'dcworkflow_scripts'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        self._initScripts(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)
        info = configurator.getWorkflowInfo(WF_ID)

        script_info = info['script_info']
        self.assertEqual(len(script_info), len(_WF_SCRIPTS))

        ids = [ x['id'] for x in script_info ]

        for k in _WF_SCRIPTS.keys():
            self.assertTrue(k in ids)

        for info in script_info:

            expected = _WF_SCRIPTS[info['id']]

            self.assertEqual(info['meta_type'], expected[0])

            if info['meta_type'] == PythonScript.meta_type:
                self.assertEqual(info['filename'], expected[2] % WF_ID)
            else:
                self.assertEqual(info['filename'], expected[2])

    def test_getWorkflowInfo_dcworkflow_creation_guard(self):
        WF_ID = 'dcworkflow_creation_guard'

        _site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        self._initCreationGuard(dcworkflow)

    def test_generateXML_empty(self):
        WF_ID = 'empty'
        WF_TITLE = 'Empty DCWorkflow'
        WF_DESCRIPTION = 'This is a empty workflow'
        WF_INITIAL_STATE = 'initial'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        dcworkflow.title = WF_TITLE
        dcworkflow.description = WF_DESCRIPTION
        dcworkflow.initial_state = WF_INITIAL_STATE

        configurator = self._makeOne(dcworkflow).__of__(site)

        self._compareDOM(configurator.generateWorkflowXML(),
                         _EMPTY_WORKFLOW_EXPORT % (WF_ID,
                                                   WF_TITLE,
                                                   WF_DESCRIPTION,
                                                   WF_INITIAL_STATE))

    def test_generateWorkflowXML_normal(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal Workflow'
        WF_INITIAL_STATE = 'closed'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID)
        dcworkflow.title = WF_TITLE
        dcworkflow.description = WF_DESCRIPTION
        dcworkflow.initial_state = WF_INITIAL_STATE
        dcworkflow.permissions = _WF_PERMISSIONS
        self._initVariables(dcworkflow)
        self._initStates(dcworkflow)
        self._initTransitions(dcworkflow)
        self._initWorklists(dcworkflow)
        self._initScripts(dcworkflow)

        configurator = self._makeOne(dcworkflow).__of__(site)

        self._compareDOM(configurator.generateWorkflowXML(),
                         _NORMAL_WORKFLOW_EXPORT
                         % {'workflow_id': WF_ID,
                            'title': WF_TITLE,
                            'description': WF_DESCRIPTION,
                            'initial_state': WF_INITIAL_STATE,
                            'workflow_filename': WF_ID.replace(' ', '_')})

    def test_generateWorkflowXML_multiple(self):
        WF_ID_1 = 'dc1'
        WF_TITLE_1 = 'Normal DCWorkflow #1'
        WF_DESCRIPTION_1 = 'Normal Number 1'
        WF_ID_2 = 'dc2'
        WF_TITLE_2 = 'Normal DCWorkflow #2'
        WF_DESCRIPTION_2 = 'Normal Numer 2'
        WF_INITIAL_STATE = 'closed'

        site, wtool = self._initSite()

        dcworkflow_1 = self._initDCWorkflow(wtool, WF_ID_1)
        dcworkflow_1.title = WF_TITLE_1
        dcworkflow_1.description = WF_DESCRIPTION_1
        dcworkflow_1.initial_state = WF_INITIAL_STATE
        dcworkflow_1.permissions = _WF_PERMISSIONS
        self._initVariables(dcworkflow_1)
        self._initStates(dcworkflow_1)
        self._initTransitions(dcworkflow_1)
        self._initWorklists(dcworkflow_1)
        self._initScripts(dcworkflow_1)

        dcworkflow_2 = self._initDCWorkflow(wtool, WF_ID_2)
        dcworkflow_2.title = WF_TITLE_2
        dcworkflow_2.description = WF_DESCRIPTION_2
        dcworkflow_2.initial_state = WF_INITIAL_STATE
        dcworkflow_2.permissions = _WF_PERMISSIONS
        self._initVariables(dcworkflow_2)
        self._initStates(dcworkflow_2)
        self._initTransitions(dcworkflow_2)
        self._initWorklists(dcworkflow_2)
        self._initScripts(dcworkflow_2)

        configurator = self._makeOne(dcworkflow_1).__of__(site)

        self._compareDOM(configurator.generateWorkflowXML(),
                         _NORMAL_WORKFLOW_EXPORT
                         % {'workflow_id': WF_ID_1,
                            'title': WF_TITLE_1,
                            'description': WF_DESCRIPTION_1,
                            'initial_state': WF_INITIAL_STATE,
                            'workflow_filename': WF_ID_1.replace(' ', '_')})

        configurator = self._makeOne(dcworkflow_2).__of__(site)

        self._compareDOM(configurator.generateWorkflowXML(),
                         _NORMAL_WORKFLOW_EXPORT
                         % {'workflow_id': WF_ID_2,
                            'title': WF_TITLE_2,
                            'description': WF_DESCRIPTION_2,
                            'initial_state': WF_INITIAL_STATE,
                            'workflow_filename': WF_ID_2.replace(' ', '_')})

    def test_parseWorkflowXML_empty(self):
        WF_ID = 'empty'
        WF_TITLE = 'Empty DCWorkflow'
        WF_DESCRIPTION = 'This is an empty workflow'
        WF_INITIAL_STATE = 'initial'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         states,
         transitions,
         variables,
         worklists,
         permissions,
         scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(_EMPTY_WORKFLOW_EXPORT
                                          % (WF_ID,
                                             WF_TITLE,
                                             WF_DESCRIPTION,
                                             WF_INITIAL_STATE))

        self.assertEqual(description, WF_DESCRIPTION)
        self.assertEqual(len(states), 0)
        self.assertEqual(len(transitions), 0)
        self.assertEqual(len(variables), 0)
        self.assertEqual(len(worklists), 0)
        self.assertEqual(len(permissions), 0)
        self.assertEqual(len(scripts), 0)

    def test_parseWorkflowXML_normal_attribs(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'This is a normal DCWorkflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (workflow_id,
         title,
         state_variable,
         initial_state,
         _states,
         _transitions,
         _variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(workflow_id, WF_ID)
        self.assertEqual(title, WF_TITLE)
        self.assertEqual(description, WF_DESCRIPTION)
        self.assertEqual(state_variable, 'state')
        self.assertEqual(initial_state, WF_INITIAL_STATE)

    def test_parseWorkflowXML_normal_states(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         states,
         _transitions,
         _variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(states), len(_WF_STATES))

        for state in states:

            state_id = state['state_id']
            self.assertTrue(state_id in _WF_STATES)

            expected = _WF_STATES[state_id]

            self.assertEqual(state['title'], expected[0])

            description = ''.join(state['description'])
            self.assertTrue(expected[1] in description)

            self.assertEqual(tuple(state['transitions']), expected[2])
            self.assertEqual(state['permissions'], expected[3])
            self.assertEqual(tuple(state['groups']), tuple(expected[4]))

            for k, v_info in state['variables'].items():

                exp_value = expected[5][k]
                self.assertEqual(v_info['value'], str(exp_value))

                if isinstance(exp_value, bool):
                    self.assertEqual(v_info['type'], 'bool')
                elif isinstance(exp_value, int):
                    self.assertEqual(v_info['type'], 'int')
                elif isinstance(exp_value, float):
                    self.assertEqual(v_info['type'], 'float')
                elif isinstance(exp_value, basestring):
                    self.assertEqual(v_info['type'], 'string')

    def test_parseWorkflowXML_state_w_missing_acquired(self):
        WF_ID = 'missing_acquired'
        WF_TITLE = 'DCWorkflow w/o acquired on state'
        WF_DESCRIPTION = WF_TITLE
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         states,
         _transitions,
         _variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _WORKFLOW_EXPORT_WO_ACQUIRED
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(states), len(_WF_STATES_MISSING_ACQUIRED))

        for state in states:

            state_id = state['state_id']
            self.assertTrue(state_id in _WF_STATES_MISSING_ACQUIRED)

            expected = _WF_STATES_MISSING_ACQUIRED[state_id]

            self.assertEqual(state['title'], expected[0])

            description = ''.join(state['description'])
            self.assertTrue(expected[1] in description)

            self.assertEqual(tuple(state['transitions']), expected[2])
            self.assertEqual(state['permissions'], expected[3])
            self.assertEqual(tuple(state['groups']), tuple(expected[4]))

    def test_parseWorkflowXML_normal_transitions(self):
        from Products.DCWorkflow.exportimport import TRIGGER_TYPES

        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         transitions,
         _variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(transitions), len(_WF_TRANSITIONS))

        for transition in transitions:

            transition_id = transition['transition_id']
            self.assertTrue(transition_id in _WF_TRANSITIONS)

            expected = _WF_TRANSITIONS[transition_id]

            self.assertEqual(transition['title'], expected[0])

            description = ''.join(transition['description'])
            self.assertTrue(expected[1] in description)

            self.assertEqual(transition['new_state'], expected[2])
            self.assertEqual(transition['trigger'], TRIGGER_TYPES[expected[3]])
            self.assertEqual(transition['before_script'], expected[4])
            self.assertEqual(transition['after_script'], expected[5])

            action = transition['action']
            self.assertEqual(action.get('name', ''), expected[6])
            self.assertEqual(action.get('url', ''), expected[7])
            self.assertEqual(action.get('icon', ''), expected[8])
            self.assertEqual(action.get('category', ''), expected[9])

            self.assertEqual(transition['variables'], expected[10])

            guard = transition['guard']
            self.assertEqual(tuple(guard.get('permissions', ())), expected[11])
            self.assertEqual(tuple(guard.get('roles', ())), expected[12])
            self.assertEqual(tuple(guard.get('groups', ())), expected[13])
            self.assertEqual(guard.get('expression', ''), expected[14])

    def test_parseWorkflowXML_normal_variables(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         _transitions,
         variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(variables), len(_WF_VARIABLES))

        for variable in variables:

            variable_id = variable['variable_id']
            self.assertTrue(variable_id in _WF_VARIABLES)

            expected = _WF_VARIABLES[variable_id]

            description = ''.join(variable['description'])
            self.assertTrue(expected[0] in description)

            default = variable['default']
            self.assertEqual(default['value'], expected[1])

            exp_type = 'n/a'

            if expected[1]:
                exp_value = expected[1]

                if isinstance(exp_value, bool):
                    exp_type = 'bool'
                elif isinstance(exp_value, int):
                    exp_type = 'int'
                elif isinstance(exp_value, float):
                    exp_type = 'float'
                elif isinstance(exp_value, basestring):
                    exp_type = 'string'
                else:
                    exp_type = 'XXX'

            self.assertEqual(default['type'], exp_type)
            self.assertEqual(default['expression'], expected[2])

            self.assertEqual(variable['for_catalog'], expected[3])
            self.assertEqual(variable['for_status'], expected[4])
            self.assertEqual(variable['update_always'], expected[5])

            guard = variable['guard']
            self.assertEqual(tuple(guard.get('permissions', ())), expected[6])
            self.assertEqual(tuple(guard.get('roles', ())), expected[7])
            self.assertEqual(tuple(guard.get('groups', ())), expected[8])
            self.assertEqual(guard.get('expression', ''), expected[9])

    def test_parseWorkflowXML_w_variables_missing_attrs(self):
        WF_ID = 'normal'
        WF_TITLE = 'DCWorkflow w/ missing attrs'
        WF_DESCRIPTION = WF_TITLE
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         _transitions,
         variables,
         _worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _WORKFLOW_EXPORT_W_MISSING_VARIABLE_ATTRS
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(variables), len(_WF_VARIABLES_MISSING_ATTRS))

        for variable in variables:

            variable_id = variable['variable_id']
            self.assertTrue(variable_id in _WF_VARIABLES_MISSING_ATTRS)

            expected = _WF_VARIABLES_MISSING_ATTRS[variable_id]

            description = ''.join(variable['description'])
            self.assertTrue(expected[0] in description)

            default = variable['default']
            self.assertEqual(default['value'], expected[1])

            exp_type = 'n/a'

            if expected[1]:
                exp_value = expected[1]

                if isinstance(exp_value, bool):
                    exp_type = 'bool'
                elif isinstance(exp_value, int):
                    exp_type = 'int'
                elif isinstance(exp_value, float):
                    exp_type = 'float'
                elif isinstance(exp_value, basestring):
                    exp_type = 'string'
                else:
                    exp_type = 'XXX'

            self.assertEqual(default['type'], exp_type)
            self.assertEqual(default['expression'], expected[2])

            self.assertEqual(variable['for_catalog'], expected[3])
            self.assertEqual(variable['for_status'], expected[4])
            self.assertEqual(variable['update_always'], expected[5])

            guard = variable['guard']
            self.assertEqual(tuple(guard.get('permissions', ())), expected[6])
            self.assertEqual(tuple(guard.get('roles', ())), expected[7])
            self.assertEqual(tuple(guard.get('groups', ())), expected[8])
            self.assertEqual(guard.get('expression', ''), expected[9])

    def test_parseWorkflowXML_normal_worklists(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         _transitions,
         _variables,
         worklists,
         _permissions,
         _scripts,
         description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(worklists), len(_WF_WORKLISTS))

        for worklist in worklists:
            worklist_id = worklist['worklist_id']
            self.assertTrue(worklist_id in _WF_WORKLISTS)

            expected = _WF_WORKLISTS[worklist_id]

            self.assertEqual(worklist['title'], expected[0])

            description = ''.join(worklist['description'])
            self.assertTrue(expected[1] in description)
            self.assertEqual(tuple(worklist['match']), tuple(expected[2]))

            action = worklist['action']
            self.assertEqual(action.get('name', ''), expected[3])
            self.assertEqual(action.get('url', ''), expected[4])
            self.assertEqual(action.get('icon', ''), expected[5])
            self.assertEqual(action.get('category', ''), expected[6])

            guard = worklist['guard']
            self.assertEqual(tuple(guard.get('permissions', ())), expected[7])
            self.assertEqual(tuple(guard.get('roles', ())), expected[8])
            self.assertEqual(tuple(guard.get('groups', ())), expected[9])
            self.assertEqual(guard.get('expression', ''), expected[10])

    def test_parseWorkflowXML_normal_permissions(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (_workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         _transitions,
         _variables,
         _worklists,
         permissions,
         _scripts,
         _description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(permissions), len(_WF_PERMISSIONS))

        for permission in permissions:
            self.assertTrue(permission in _WF_PERMISSIONS)

    def test_parseWorkflowXML_normal_scripts(self):
        WF_ID = 'normal'
        WF_TITLE = 'Normal DCWorkflow'
        WF_DESCRIPTION = 'Normal workflow'
        WF_INITIAL_STATE = 'closed'

        site, _wtool = self._initSite()

        configurator = self._makeOne(site).__of__(site)

        (workflow_id,
         _title,
         _state_variable,
         _initial_state,
         _states,
         _transitions,
         _variables,
         _worklists,
         _permissions,
         scripts,
         _description,
         _manager_bypass,
         _creation_guard
        ) = configurator.parseWorkflowXML(
                          _NORMAL_WORKFLOW_EXPORT
                          % {'workflow_id': WF_ID,
                             'title': WF_TITLE,
                             'description': WF_DESCRIPTION,
                             'initial_state': WF_INITIAL_STATE,
                             'workflow_filename': WF_ID.replace(' ', '_')})

        self.assertEqual(len(scripts), len(_WF_SCRIPTS))

        for script in scripts:
            script_id = script['script_id']
            self.assertTrue(script_id in _WF_SCRIPTS)

            expected = _WF_SCRIPTS[script_id]

            self.assertEqual(script['meta_type'], expected[0])

            # Body is not kept as part of the workflow XML

            if script['meta_type'] == PythonScript.meta_type:
                self.assertEqual(script['filename'], expected[2] % workflow_id)
            else:
                self.assertEqual(script['filename'], expected[2])


_WF_PERMISSIONS = (
    'Open content for modifications',
    'Modify content',
    'Query history',
    'Restore expired content')

_WF_GROUPS = (
    'Content_owners',
    'Content_assassins')

_WF_VARIABLES = {
    'when_opened': (
        'Opened when',
        '',
        "python:None",
        True,
        False,
        True,
        ('Query history', 'Open content for modifications'),
        (),
        (),
        ""),
    'when_expired': (
        'Expired when',
        '',
        "nothing",
        True,
        False,
        True,
        ('Query history', 'Open content for modifications'),
        (),
        (),
        ""),
    'killed_by': (
        'Killed by',
        'n/a',
        "",
        True,
        False,
        True,
        (),
        ('Hangman', 'Sherrif'),
        (),
        "")
}

_WF_VARIABLES_MISSING_ATTRS = {
    'when_opened': (
        'Opened when',
        '',
        "python:None",
        False,
        False,
        False,
        ('Query history', 'Open content for modifications'),
        (),
        (),
        ""),
    'when_expired': (
        'Expired when',
        '',
        "nothing",
        False,
        False,
        False,
        ('Query history', 'Open content for modifications'),
        (),
        (),
        ""),
    'killed_by': (
        'Killed by',
        'n/a',
        "",
        False,
        False,
        False,
        (),
        ('Hangman', 'Sherrif'),
        (),
        "")}

_WF_STATES = {
    'closed': (
        'Closed',
        'Closed for modifications',
        ('open', 'kill', 'expire'),
        {'Modify content': ()},
        (),
        {'is_opened': False, 'is_closed': True}),
    'opened': (
        'Opened',
        'Open for modifications',
        ('close', 'kill', 'expire'),
        {'Modify content': ['Owner', 'Manager']},
        [('Content_owners', ('Owner',))],
        {'is_opened': True, 'is_closed': False}),
    'killed': (
        'Killed',
        'Permanently unavailable',
        (),
        {},
        (),
        {}),
    'expired': (
        'Expired',
        'Expiration date has passed',
        ('open',),
        {'Modify content': ['Owner', 'Manager']},
        (),
        {'is_opened': False, 'is_closed': False})}

_WF_STATES_MISSING_ACQUIRED = {
    'closed': (
        'Closed',
        'Closed for modifications',
        ('open', 'kill', 'expire'),
        {'Modify content': ()},
        (),
        {'is_opened': False, 'is_closed': True}),
    'opened': (
        'Opened',
        'Open for modifications',
        ('close', 'kill', 'expire'),
        {'Modify content': ('Owner', 'Manager')},
        [('Content_owners', ('Owner',))],
        {'is_opened': True, 'is_closed': False}),
    'killed': (
        'Killed',
        'Permanently unavailable',
        (),
        {},
        (),
        {}),
    'expired': (
        'Expired',
        'Expiration date has passed',
        ('open',),
        {'Modify content': ('Owner', 'Manager')},
        (),
        {'is_opened': False, 'is_closed': False})}

_WF_TRANSITIONS = {
    'open': (
        'Open',
        'Open the object for modifications',
        'opened',
        TRIGGER_USER_ACTION,
        'before_open',
        '',
        'Open',
        'string:${object_url}/open_for_modifications',
        'string:${portal_url}/open.png',
        'workflow',
        {'when_opened': 'object/ZopeTime'},
        ('Open content for modifications',),
        (),
        (),
        ""),
    'close': (
        'Close',
        'Close the object for modifications',
        'closed',
        TRIGGER_USER_ACTION,
        '',
        'after_close',
        'Close',
        'string:${object_url}/close_for_modifications',
        'string:${portal_url}/close.png',
        'workflow',
        {},
        (),
        ('Owner', 'Manager'),
        (),
        ""),
    'kill': (
        'Kill',
        'Make the object permanently unavailable.',
        'killed',
        TRIGGER_USER_ACTION,
        '',
        'after_kill',
        'Kill',
        'string:${object_url}/kill_object',
        'string:${portal_url}/kill.png',
        'workflow',
        {'killed_by': 'string:${user/getId}'},
        (),
        (),
        ('Content_assassins',),
        ""),
    'expire': (
        'Expire',
        'Retire objects whose expiration is past.',
        'expired',
        TRIGGER_AUTOMATIC,
        'before_expire',
        '',
        '',
        '',
        '',
        '',
        {'when_expired': 'object/ZopeTime'},
        (),
        (),
        (),
        "python: object.expiration() <= object.ZopeTime()")}

_WF_WORKLISTS = {
    'expired_list': (
        'Expired',
        'Worklist for expired content',
        {'state': ('expired',)},
        'Expired items',
        'string:${portal_url}/expired_items',
        'string:${portal_url}/expired.png',
        'workflow',
        ('Restore expired content',),
        (),
        (),
        ""),
    'alive_list': (
        'Alive',
        'Worklist for content not yet expired / killed',
        {'state': ('open', 'closed')},
        'Expired items',
        'string:${portal_url}/expired_items',
        'string:${portal_url}/alive.png',
        'workflow',
        ('Restore expired content',),
        (),
        (),
        "")}

_BEFORE_OPEN_SCRIPT = """\
## Script (Python) "before_open"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
return 'before_open'
"""

_AFTER_CLOSE_SCRIPT = """\
## Script (Python) "after_close"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
return 'after_close'
"""

_AFTER_KILL_SCRIPT = """\
## Script (Python) "after_kill"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=
##
return 'after_kill'
"""

_WF_SCRIPTS = {
    'before_open': (
        PythonScript.meta_type,
        _BEFORE_OPEN_SCRIPT,
        'workflows/%s/scripts/before_open.py',
        None,
        None),
    'after_close': (
        PythonScript.meta_type,
        _AFTER_CLOSE_SCRIPT,
        'workflows/%s/scripts/after_close.py',
        None,
        None),
    'after_kill': (
        PythonScript.meta_type,
        _AFTER_KILL_SCRIPT,
        'workflows/%s/scripts/after_kill.py',
        None,
        None),
    'before_expire': (
        ExternalMethod.meta_type,
        '',
        '',
        'DCWorkflow.test_method',
        'test')}

_CREATION_GUARD = (
    ('Add portal content', 'Manage portal'),
    ('Owner', 'Manager'),
    ('group_readers', 'group_members'),
    'python:len(here.objectIds() <= 10)')

_NORMAL_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <property name="title"></property>
 <object name="Non-DCWorkflow" meta_type="Dummy Workflow"/>
 <object name="dcworkflow" meta_type="Workflow"/>
 <bindings>
  <default/>
 </bindings>
</object>
"""

_NORMAL_TOOL_EXPORT_WITH_FILENAME = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <property name="title"></property>
 <object name="Non-DCWorkflow" meta_type="Dummy Workflow"/>
 <object name="%(workflow_id)s" meta_type="Workflow"/>
 <bindings>
  <default/>
 </bindings>
</object>
"""

_FILENAME_TOOL_EXPORT = """\
<?xml version="1.0"?>
<object name="portal_workflow" meta_type="Dummy Workflow Tool">
 <property name="title"></property>
 <object name="name with spaces" meta_type="Workflow"/>
 <bindings>
  <default/>
 </bindings>
</object>
"""

_EMPTY_WORKFLOW_EXPORT = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%s"
    title="%s"
    description="%s"
    state_variable="state"
    initial_state="%s"
    manager_bypass="False">
</dc-workflow>
"""

# Make sure old exports are still imported well. Changes:
# - scripts are now in in a 'scripts' subdirectory
_OLD_WORKFLOW_EXPORT = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%(workflow_id)s"
    title="%(title)s"
    state_variable="state"
    initial_state="%(initial_state)s"
    manager_bypass="False">
 <permission>Open content for modifications</permission>
 <permission>Modify content</permission>
 <permission>Query history</permission>
 <permission>Restore expired content</permission>
 <state
    state_id="closed"
    title="Closed">
  <description>Closed for modifications</description>
  <exit-transition
    transition_id="open"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="False"
    name="Modify content">
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">True</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="expired"
    title="Expired">
  <description>Expiration date has passed</description>
  <exit-transition
    transition_id="open"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="killed"
    title="Killed">
  <description>Permanently unavailable</description>
 </state>
 <state
    state_id="opened"
    title="Opened">
  <description>Open for modifications</description>
  <exit-transition
    transition_id="close"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <group-map name="Content_owners">
   <group-role>Owner</group-role>
  </group-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">True</assignment>
 </state>
 <transition
    transition_id="close"
    title="Close"
    trigger="USER"
    new_state="closed"
    before_script=""
    after_script="after_close">
  <description>Close the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/close_for_modifications">Close</action>
  <guard>
   <guard-role>Owner</guard-role>
   <guard-role>Manager</guard-role>
  </guard>
 </transition>
 <transition
    transition_id="expire"
    title="Expire"
    trigger="AUTOMATIC"
    new_state="expired"
    before_script="before_expire"
    after_script="">
  <description>Retire objects whose expiration is past.</description>
  <guard>
   <guard-expression>python: object.expiration() &lt;= object.ZopeTime()</guard-expression>
  </guard>
  <assignment
    name="when_expired">object/ZopeTime</assignment>
 </transition>
 <transition
    transition_id="kill"
    title="Kill"
    trigger="USER"
    new_state="killed"
    before_script=""
    after_script="after_kill">
  <description>Make the object permanently unavailable.</description>
  <action
    category="workflow"
    url="string:${object_url}/kill_object">Kill</action>
  <guard>
   <guard-group>Content_assassins</guard-group>
  </guard>
  <assignment
    name="killed_by">string:${user/getId}</assignment>
 </transition>
 <transition
    transition_id="open"
    title="Open"
    trigger="USER"
    new_state="opened"
    before_script="before_open"
    after_script="">
  <description>Open the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/open_for_modifications">Open</action>
  <guard>
   <guard-permission>Open content for modifications</guard-permission>
  </guard>
  <assignment
    name="when_opened">object/ZopeTime</assignment>
 </transition>
 <worklist
    worklist_id="alive_list"
    title="Alive">
  <description>Worklist for content not yet expired / killed</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="open; closed"/>
 </worklist>
 <worklist
    worklist_id="expired_list"
    title="Expired">
  <description>Worklist for expired content</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="expired"/>
 </worklist>
 <variable
    variable_id="killed_by"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Killed by</description>
   <default>
    <value type="string">n/a</value>
   </default>
   <guard>
    <guard-role>Hangman</guard-role>
    <guard-role>Sherrif</guard-role>
   </guard>
 </variable>
 <variable
    variable_id="when_expired"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Expired when</description>
   <default>
    <expression>nothing</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <variable
    variable_id="when_opened"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Opened when</description>
   <default>
    <expression>python:None</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <script
    script_id="after_close"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/after_close.py"
    module=""
    function=""
    />
 <script
    script_id="after_kill"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/after_kill.py"
    module=""
    function=""
    />
 <script
    script_id="before_expire"
    type="External Method"
    filename=""
    module="DCWorkflow.test_method"
    function="test"
    />
 <script
    script_id="before_open"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/before_open.py"
    module=""
    function=""
    />
</dc-workflow>
"""

_NORMAL_WORKFLOW_EXPORT = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%(workflow_id)s"
    title="%(title)s"
    description="%(description)s"
    state_variable="state"
    initial_state="%(initial_state)s"
    manager_bypass="False">
 <permission>Open content for modifications</permission>
 <permission>Modify content</permission>
 <permission>Query history</permission>
 <permission>Restore expired content</permission>
 <state
    state_id="closed"
    title="Closed">
  <description>Closed for modifications</description>
  <exit-transition
    transition_id="open"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="False"
    name="Modify content">
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">True</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="expired"
    title="Expired">
  <description>Expiration date has passed</description>
  <exit-transition
    transition_id="open"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="killed"
    title="Killed">
  <description>Permanently unavailable</description>
 </state>
 <state
    state_id="opened"
    title="Opened">
  <description>Open for modifications</description>
  <exit-transition
    transition_id="close"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <group-map name="Content_owners">
   <group-role>Owner</group-role>
  </group-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">True</assignment>
 </state>
 <transition
    transition_id="close"
    title="Close"
    trigger="USER"
    new_state="closed"
    before_script=""
    after_script="after_close">
  <description>Close the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/close_for_modifications"
    icon="string:${portal_url}/close.png">Close</action>
  <guard>
   <guard-role>Owner</guard-role>
   <guard-role>Manager</guard-role>
  </guard>
 </transition>
 <transition
    transition_id="expire"
    title="Expire"
    trigger="AUTOMATIC"
    new_state="expired"
    before_script="before_expire"
    after_script="">
  <description>Retire objects whose expiration is past.</description>
  <guard>
   <guard-expression>python: object.expiration() &lt;= object.ZopeTime()</guard-expression>
  </guard>
  <assignment
    name="when_expired">object/ZopeTime</assignment>
 </transition>
 <transition
    transition_id="kill"
    title="Kill"
    trigger="USER"
    new_state="killed"
    before_script=""
    after_script="after_kill">
  <description>Make the object permanently unavailable.</description>
  <action
    category="workflow"
    url="string:${object_url}/kill_object"
    icon="string:${portal_url}/kill.png">Kill</action>
  <guard>
   <guard-group>Content_assassins</guard-group>
  </guard>
  <assignment
    name="killed_by">string:${user/getId}</assignment>
 </transition>
 <transition
    transition_id="open"
    title="Open"
    trigger="USER"
    new_state="opened"
    before_script="before_open"
    after_script="">
  <description>Open the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/open_for_modifications"
    icon="string:${portal_url}/open.png">Open</action>
  <guard>
   <guard-permission>Open content for modifications</guard-permission>
  </guard>
  <assignment
    name="when_opened">object/ZopeTime</assignment>
 </transition>
 <worklist
    worklist_id="alive_list"
    title="Alive">
  <description>Worklist for content not yet expired / killed</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/alive.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="open; closed"/>
 </worklist>
 <worklist
    worklist_id="expired_list"
    title="Expired">
  <description>Worklist for expired content</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/expired.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="expired"/>
 </worklist>
 <variable
    variable_id="killed_by"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Killed by</description>
   <default>
    <value type="string">n/a</value>
   </default>
   <guard>
    <guard-role>Hangman</guard-role>
    <guard-role>Sherrif</guard-role>
   </guard>
 </variable>
 <variable
    variable_id="when_expired"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Expired when</description>
   <default>
    <expression>nothing</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <variable
    variable_id="when_opened"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Opened when</description>
   <default>
    <expression>python:None</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <script
    script_id="after_close"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_close.py"
    module=""
    function=""
    />
 <script
    script_id="after_kill"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_kill.py"
    module=""
    function=""
    />
 <script
    script_id="before_expire"
    type="External Method"
    filename=""
    module="DCWorkflow.test_method"
    function="test"
    />
 <script
    script_id="before_open"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/before_open.py"
    module=""
    function=""
    />
</dc-workflow>
"""

_WORKFLOW_EXPORT_WO_ACQUIRED = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%(workflow_id)s"
    title="%(title)s"
    description="%(description)s"
    state_variable="state"
    initial_state="%(initial_state)s"
    manager_bypass="False">
 <permission>Open content for modifications</permission>
 <permission>Modify content</permission>
 <permission>Query history</permission>
 <permission>Restore expired content</permission>
 <state
    state_id="closed"
    title="Closed">
  <description>Closed for modifications</description>
  <exit-transition
    transition_id="open"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    name="Modify content">
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">True</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="expired"
    title="Expired">
  <description>Expiration date has passed</description>
  <exit-transition
    transition_id="open"/>
  <permission-map
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="killed"
    title="Killed">
  <description>Permanently unavailable</description>
 </state>
 <state
    state_id="opened"
    title="Opened">
  <description>Open for modifications</description>
  <exit-transition
    transition_id="close"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <group-map name="Content_owners">
   <group-role>Owner</group-role>
  </group-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">True</assignment>
 </state>
 <transition
    transition_id="close"
    title="Close"
    trigger="USER"
    new_state="closed"
    before_script=""
    after_script="after_close">
  <description>Close the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/close_for_modifications"
    icon="string:${portal_url}/close.png">Close</action>
  <guard>
   <guard-role>Owner</guard-role>
   <guard-role>Manager</guard-role>
  </guard>
 </transition>
 <transition
    transition_id="expire"
    title="Expire"
    trigger="AUTOMATIC"
    new_state="expired"
    before_script="before_expire"
    after_script="">
  <description>Retire objects whose expiration is past.</description>
  <guard>
   <guard-expression>python: object.expiration() &lt;= object.ZopeTime()</guard-expression>
  </guard>
  <assignment
    name="when_expired">object/ZopeTime</assignment>
 </transition>
 <transition
    transition_id="kill"
    title="Kill"
    trigger="USER"
    new_state="killed"
    before_script=""
    after_script="after_kill">
  <description>Make the object permanently unavailable.</description>
  <action
    category="workflow"
    url="string:${object_url}/kill_object"
    icon="string:${portal_url}/kill.png">Kill</action>
  <guard>
   <guard-group>Content_assassins</guard-group>
  </guard>
  <assignment
    name="killed_by">string:${user/getId}</assignment>
 </transition>
 <transition
    transition_id="open"
    title="Open"
    trigger="USER"
    new_state="opened"
    before_script="before_open"
    after_script="">
  <description>Open the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/open_for_modifications"
    icon="string:${portal_url}/open.png">Open</action>
  <guard>
   <guard-permission>Open content for modifications</guard-permission>
  </guard>
  <assignment
    name="when_opened">object/ZopeTime</assignment>
 </transition>
 <worklist
    worklist_id="alive_list"
    title="Alive">
  <description>Worklist for content not yet expired / killed</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/alive.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="open; closed"/>
 </worklist>
 <worklist
    worklist_id="expired_list"
    title="Expired">
  <description>Worklist for expired content</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/expired.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="expired"/>
 </worklist>
 <variable
    variable_id="killed_by"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Killed by</description>
   <default>
    <value type="string">n/a</value>
   </default>
   <guard>
    <guard-role>Hangman</guard-role>
    <guard-role>Sherrif</guard-role>
   </guard>
 </variable>
 <variable
    variable_id="when_expired"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Expired when</description>
   <default>
    <expression>nothing</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <variable
    variable_id="when_opened"
    for_catalog="True"
    for_status="False"
    update_always="True">
   <description>Opened when</description>
   <default>
    <expression>python:None</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <script
    script_id="after_close"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_close.py"
    module=""
    function=""
    />
 <script
    script_id="after_kill"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_kill.py"
    module=""
    function=""
    />
 <script
    script_id="before_expire"
    type="External Method"
    filename=""
    module="DCWorkflow.test_method"
    function="test"
    />
 <script
    script_id="before_open"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/before_open.py"
    module=""
    function=""
    />
</dc-workflow>
"""

_WORKFLOW_EXPORT_W_MISSING_VARIABLE_ATTRS = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%(workflow_id)s"
    title="%(title)s"
    description="%(description)s"
    state_variable="state"
    initial_state="%(initial_state)s"
    manager_bypass="False">
 <permission>Open content for modifications</permission>
 <permission>Modify content</permission>
 <permission>Query history</permission>
 <permission>Restore expired content</permission>
 <state
    state_id="closed"
    title="Closed">
  <description>Closed for modifications</description>
  <exit-transition
    transition_id="open"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="False"
    name="Modify content">
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">True</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="expired"
    title="Expired">
  <description>Expiration date has passed</description>
  <exit-transition
    transition_id="open"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">False</assignment>
 </state>
 <state
    state_id="killed"
    title="Killed">
  <description>Permanently unavailable</description>
 </state>
 <state
    state_id="opened"
    title="Opened">
  <description>Open for modifications</description>
  <exit-transition
    transition_id="close"/>
  <exit-transition
    transition_id="kill"/>
  <exit-transition
    transition_id="expire"/>
  <permission-map
    acquired="True"
    name="Modify content">
   <permission-role>Owner</permission-role>
   <permission-role>Manager</permission-role>
  </permission-map>
  <group-map name="Content_owners">
   <group-role>Owner</group-role>
  </group-map>
  <assignment
    name="is_closed"
    type="bool">False</assignment>
  <assignment
    name="is_opened"
    type="bool">True</assignment>
 </state>
 <transition
    transition_id="close"
    title="Close"
    trigger="USER"
    new_state="closed"
    before_script=""
    after_script="after_close">
  <description>Close the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/close_for_modifications"
    icon="string:${portal_url}/close.png">Close</action>
  <guard>
   <guard-role>Owner</guard-role>
   <guard-role>Manager</guard-role>
  </guard>
 </transition>
 <transition
    transition_id="expire"
    title="Expire"
    trigger="AUTOMATIC"
    new_state="expired"
    before_script="before_expire"
    after_script="">
  <description>Retire objects whose expiration is past.</description>
  <guard>
   <guard-expression>python: object.expiration() &lt;= object.ZopeTime()</guard-expression>
  </guard>
  <assignment
    name="when_expired">object/ZopeTime</assignment>
 </transition>
 <transition
    transition_id="kill"
    title="Kill"
    trigger="USER"
    new_state="killed"
    before_script=""
    after_script="after_kill">
  <description>Make the object permanently unavailable.</description>
  <action
    category="workflow"
    url="string:${object_url}/kill_object"
    icon="string:${portal_url}/kill.png">Kill</action>
  <guard>
   <guard-group>Content_assassins</guard-group>
  </guard>
  <assignment
    name="killed_by">string:${user/getId}</assignment>
 </transition>
 <transition
    transition_id="open"
    title="Open"
    trigger="USER"
    new_state="opened"
    before_script="before_open"
    after_script="">
  <description>Open the object for modifications</description>
  <action
    category="workflow"
    url="string:${object_url}/open_for_modifications"
    icon="string:${portal_url}/open.png">Open</action>
  <guard>
   <guard-permission>Open content for modifications</guard-permission>
  </guard>
  <assignment
    name="when_opened">object/ZopeTime</assignment>
 </transition>
 <worklist
    worklist_id="alive_list"
    title="Alive">
  <description>Worklist for content not yet expired / killed</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/alive.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="open; closed"/>
 </worklist>
 <worklist
    worklist_id="expired_list"
    title="Expired">
  <description>Worklist for expired content</description>
  <action
    category="workflow"
    url="string:${portal_url}/expired_items"
    icon="string:${portal_url}/expired.png">Expired items</action>
  <guard>
   <guard-permission>Restore expired content</guard-permission>
  </guard>
  <match name="state" values="expired"/>
 </worklist>
 <variable
    variable_id="killed_by">
   <description>Killed by</description>
   <default>
    <value type="string">n/a</value>
   </default>
   <guard>
    <guard-role>Hangman</guard-role>
    <guard-role>Sherrif</guard-role>
   </guard>
 </variable>
 <variable
    variable_id="when_expired">
   <description>Expired when</description>
   <default>
    <expression>nothing</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <variable
    variable_id="when_opened">
   <description>Opened when</description>
   <default>
    <expression>python:None</expression>
   </default>
   <guard>
    <guard-permission>Query history</guard-permission>
    <guard-permission>Open content for modifications</guard-permission>
   </guard>
 </variable>
 <script
    script_id="after_close"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_close.py"
    module=""
    function=""
    />
 <script
    script_id="after_kill"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/after_kill.py"
    module=""
    function=""
    />
 <script
    script_id="before_expire"
    type="External Method"
    filename=""
    module="DCWorkflow.test_method"
    function="test"
    />
 <script
    script_id="before_open"
    type="Script (Python)"
    filename="workflows/%(workflow_filename)s/scripts/before_open.py"
    module=""
    function=""
    />
</dc-workflow>
"""

_CREATION_GUARD_WORKFLOW_EXPORT = """\
<?xml version="1.0"?>
<dc-workflow
    workflow_id="%s"
    title="%s"
    description="%s"
    state_variable="state"
    initial_state="%s"
    manager_bypass="True">
 <instance-creation-conditions>
  <guard>
   <guard-permission>Add portal content</guard-permission>
   <guard-role>Owner</guard-role>
   <guard-group>group_members</guard-group>
   <guard-expression>python:len(here.objectIds() &lt;= 10)</guard-expression>
  </guard>
 </instance-creation-conditions>
</dc-workflow>
"""


class Test_exportWorkflow(_WorkflowSetup, _GuardChecker):

    layer = ExportImportZCMLLayer

    def test_empty(self):
        from Products.CMFCore.exportimport.workflow import exportWorkflowTool

        site, _wtool = self._initSite()
        context = DummyExportContext(site)
        exportWorkflowTool(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'workflows.xml')
        self._compareDOM(text, _EMPTY_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from Products.CMFCore.exportimport.workflow import exportWorkflowTool

        WF_ID_NON = 'non_dcworkflow'
        WF_TITLE_NON = 'Non-DCWorkflow'
        WF_DESCRIPTION_NON = 'Not a DCWorkflow'
        WF_ID_DC = 'dcworkflow'
        WF_TITLE_DC = 'DCWorkflow'
        WF_DESCRIPTION_DC = 'I am a DCWorkflow'
        WF_INITIAL_STATE = 'closed'

        site, wtool = self._initSite()

        nondcworkflow = DummyWorkflow(WF_TITLE_NON)
        nondcworkflow.title = WF_TITLE_NON
        nondcworkflow.description = WF_DESCRIPTION_NON
        wtool._setObject(WF_ID_NON, nondcworkflow)

        dcworkflow = self._initDCWorkflow(wtool, WF_ID_DC)
        dcworkflow.title = WF_TITLE_DC
        dcworkflow.description = WF_DESCRIPTION_DC
        dcworkflow.initial_state = WF_INITIAL_STATE
        dcworkflow.permissions = _WF_PERMISSIONS
        self._initVariables(dcworkflow)
        self._initStates(dcworkflow)
        self._initTransitions(dcworkflow)
        self._initWorklists(dcworkflow)
        self._initScripts(dcworkflow)

        context = DummyExportContext(site)
        exportWorkflowTool(context)

        # workflows list, wf defintion and 3 scripts
        self.assertEqual(len(context._wrote), 6)

        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'workflows.xml')
        self._compareDOM(text, _NORMAL_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'workflows/%s/definition.xml' % WF_ID_DC)
        self._compareDOM(text,
                         _NORMAL_WORKFLOW_EXPORT
                         % {'workflow_id': WF_ID_DC,
                            'title': WF_TITLE_DC,
                            'description': WF_DESCRIPTION_DC,
                            'initial_state': WF_INITIAL_STATE,
                            'workflow_filename': WF_ID_DC.replace(' ', '_')})
        self.assertEqual(content_type, 'text/xml')

        # just testing first script
        filename, text, content_type = context._wrote[3]
        self.assertEqual(filename,
                         'workflows/%s/scripts/after_close.py' % WF_ID_DC)
        self.assertEqual(text, _AFTER_CLOSE_SCRIPT)
        self.assertEqual(content_type, 'text/plain')

    def test_with_filenames(self):
        from Products.CMFCore.exportimport.workflow import exportWorkflowTool

        WF_ID_DC = 'name with spaces'
        WF_TITLE_DC = 'DCWorkflow with spaces'
        WF_DESCRIPTION_DC = 'Workflow w/spaces'
        WF_INITIAL_STATE = 'closed'

        site, wtool = self._initSite()
        dcworkflow = self._initDCWorkflow(wtool, WF_ID_DC)
        dcworkflow.title = WF_TITLE_DC
        dcworkflow.description = WF_DESCRIPTION_DC
        dcworkflow.initial_state = WF_INITIAL_STATE
        dcworkflow.permissions = _WF_PERMISSIONS
        self._initVariables(dcworkflow)
        self._initStates(dcworkflow)
        self._initTransitions(dcworkflow)
        self._initWorklists(dcworkflow)
        self._initScripts(dcworkflow)

        context = DummyExportContext(site)
        exportWorkflowTool(context)

        # workflows list, wf defintion and 3 scripts
        self.assertEqual(len(context._wrote), 5)

        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'workflows.xml')
        self._compareDOM(text, _FILENAME_TOOL_EXPORT)
        self.assertEqual(content_type, 'text/xml')

        filename, text, content_type = context._wrote[1]
        self.assertEqual(filename, 'workflows/name_with_spaces/definition.xml')
        self._compareDOM(text,
                         _NORMAL_WORKFLOW_EXPORT
                         % {'workflow_id': WF_ID_DC,
                            'title': WF_TITLE_DC,
                            'description': WF_DESCRIPTION_DC,
                            'initial_state': WF_INITIAL_STATE,
                            'workflow_filename': WF_ID_DC.replace(' ', '_')})
        self.assertEqual(content_type, 'text/xml')

        # just testing first script
        filename, text, content_type = context._wrote[2]
        self.assertEqual(filename, 'workflows/%s/scripts/after_close.py' %
                          WF_ID_DC.replace(' ', '_'))
        self.assertEqual(text, _AFTER_CLOSE_SCRIPT)
        self.assertEqual(content_type, 'text/plain')


class Test_importWorkflow(_WorkflowSetup, _GuardChecker):

    layer = ExportImportZCMLLayer

    def _importNormalWorkflow(self, wf_id, wf_title,
                               wf_description, wf_initial_state):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        _site, context = self._prepareImportNormalWorkflow(
            wf_id, wf_title, wf_description, wf_initial_state)

        importWorkflowTool(context)

        return self.wtool

    def _prepareImportNormalWorkflow(self, wf_id, wf_title, wf_description,
                                     wf_initial_state, site=None, purge=True):
        if site is None:
            site, wtool = self._initSite()
            self.wtool = wtool
        workflow_filename = wf_id.replace(' ', '_')

        context = DummyImportContext(site, purge=purge)
        context._files['workflows.xml'
                      ] = (_NORMAL_TOOL_EXPORT_WITH_FILENAME
                           % {'workflow_id': wf_id})

        context._files['workflows/%s/definition.xml' % workflow_filename
                      ] = (_NORMAL_WORKFLOW_EXPORT
                           % {'workflow_id': wf_id,
                              'title': wf_title,
                              'description': wf_description,
                              'initial_state': wf_initial_state,
                              'workflow_filename': workflow_filename})

        context._files['workflows/%s/scripts/after_close.py'
                       % workflow_filename] = _AFTER_CLOSE_SCRIPT

        context._files['workflows/%s/scripts/after_kill.py'
                       % workflow_filename] = _AFTER_KILL_SCRIPT

        context._files['workflows/%s/scripts/before_open.py'
                       % workflow_filename] = _BEFORE_OPEN_SCRIPT

        return site, context

    def _importOldWorkflow(self, wf_id, wf_title, wf_initial_state):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        site, wf_tool = self._initSite()
        workflow_filename = wf_id.replace(' ', '_')

        context = DummyImportContext(site)
        context._files['workflows.xml'
                      ] = (_NORMAL_TOOL_EXPORT_WITH_FILENAME
                            % {'workflow_id': wf_id})

        context._files['workflows/%s/definition.xml' % workflow_filename
                      ] = (_OLD_WORKFLOW_EXPORT
                           % {'workflow_id': wf_id,
                              'title': wf_title,
                              'initial_state': wf_initial_state,
                              'workflow_filename': workflow_filename})

        context._files['workflows/%s/after_close.py' % workflow_filename
                      ] = _AFTER_CLOSE_SCRIPT

        context._files['workflows/%s/after_kill.py' % workflow_filename
                      ] = _AFTER_KILL_SCRIPT

        context._files['workflows/%s/before_open.py' % workflow_filename
                      ] = _BEFORE_OPEN_SCRIPT

        importWorkflowTool(context)

        return wf_tool

    def test_empty_default_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site, wf_tool = self._initSite()

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site)
        context._files['workflows.xml'] = _EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 0)
        self.assertEqual(len(wf_tool._default_chain), 0)
        self.assertEqual(len(wf_tool._chains_by_type), 0)

    def test_empty_explicit_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site, wf_tool = self._initSite()

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, True)
        context._files['workflows.xml'] = _EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 0)
        self.assertEqual(len(wf_tool._default_chain), 0)
        self.assertEqual(len(wf_tool._chains_by_type), 0)

    def test_empty_skip_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site, wf_tool = self._initSite()

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, False)
        context._files['typestool.xml'] = _EMPTY_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 4)
        self.assertEqual(len(wf_tool._default_chain), 1)
        self.assertEqual(wf_tool._default_chain[0], WF_ID_NON % 1)
        self.assertEqual(len(wf_tool._chains_by_type), 1)
        self.assertEqual(wf_tool._chains_by_type['sometype'], (WF_ID_NON % 2,))

    def test_bindings_skip_purge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID_NON = 'non_dcworkflow_%s'
        WF_TITLE_NON = 'Non-DCWorkflow #%s'

        site, wf_tool = self._initSite()

        for i in range(4):
            nondcworkflow = DummyWorkflow(WF_TITLE_NON % i)
            nondcworkflow.title = WF_TITLE_NON % i
            wf_tool._setObject(WF_ID_NON % i, nondcworkflow)

        wf_tool._default_chain = (WF_ID_NON % 1,)
        wf_tool._chains_by_type['sometype'] = (WF_ID_NON % 2,)
        self.assertEqual(len(wf_tool.objectIds()), 4)

        context = DummyImportContext(site, False)
        context._files['workflows.xml'] = _BINDINGS_TOOL_EXPORT
        importWorkflowTool(context)

        self.assertEqual(len(wf_tool.objectIds()), 4)
        self.assertEqual(len(wf_tool._default_chain), 2)
        self.assertEqual(wf_tool._default_chain[0], WF_ID_NON % 0)
        self.assertEqual(wf_tool._default_chain[1], WF_ID_NON % 1)
        self.assertEqual(len(wf_tool._chains_by_type), 2)
        self.assertEqual(wf_tool._chains_by_type['sometype'],
                         (WF_ID_NON % 2,))
        self.assertEqual(wf_tool._chains_by_type['anothertype'],
                         (WF_ID_NON % 3,))

    def test_import_twice_nopurge(self):
        from Products.CMFCore.exportimport.workflow import importWorkflowTool

        WF_ID = 'dcworkflow_purge'
        WF_TITLE = 'DC Workflow testing purge'
        WF_DESCRIPTION = 'Test Purge'
        WF_INITIAL_STATE = 'closed'

        # Import a first time
        site, context = self._prepareImportNormalWorkflow(
            WF_ID, WF_TITLE, WF_DESCRIPTION, WF_INITIAL_STATE)
        importWorkflowTool(context)

        # Now reimport without purge
        site, context = self._prepareImportNormalWorkflow(
            WF_ID, WF_TITLE, WF_DESCRIPTION, WF_INITIAL_STATE,
            site=site, purge=False)
        importWorkflowTool(context)
        workflow = self.wtool.objectValues()[1]

        self.assertEqual(workflow.getId(), WF_ID)
        self.assertEqual(workflow.meta_type, DCWorkflowDefinition.meta_type)
        self.assertEqual(workflow.title, WF_TITLE)
        self.assertEqual(workflow.state_var, 'state')
        self.assertEqual(workflow.initial_state, WF_INITIAL_STATE)
        self.assertEqual(len(workflow.variables.objectItems()),
                         len(_WF_VARIABLES))
        self.assertEqual(len(workflow.states.objectItems()),
                         len(_WF_STATES))
        self.assertEqual(len(workflow.transitions.objectItems()),
                         len(_WF_TRANSITIONS))
        self.assertEqual(len(workflow.permissions),
                         len(_WF_PERMISSIONS))
        self.assertEqual(len(workflow.scripts.objectItems()),
                         len(_WF_SCRIPTS))
        self.assertEqual(len(workflow.worklists.objectItems()),
                         len(_WF_WORKLISTS))

    def test_from_empty_dcworkflow_top_level(self):
        WF_ID = 'dcworkflow_tool'
        WF_TITLE = 'DC Workflow testing tool'
        WF_DESCRIPTION = 'Testing Tool'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        self.assertEqual(len(tool.objectIds()), 2)
        self.assertEqual(tool.objectIds()[1], WF_ID)

    def test_from_empty_dcworkflow_workflow_attrs(self):
        WF_ID = 'dcworkflow_attrs'
        WF_TITLE = 'DC Workflow testing attrs'
        WF_DESCRIPTION = 'Testing Attributes'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]
        self.assertEqual(workflow.meta_type, DCWorkflowDefinition.meta_type)
        self.assertEqual(workflow.title, WF_TITLE)
        self.assertEqual(workflow.state_var, 'state')
        self.assertEqual(workflow.initial_state, WF_INITIAL_STATE)

    def test_from_empty_dcworkflow_workflow_permissions(self):
        WF_ID = 'dcworkflow_permissions'
        WF_TITLE = 'DC Workflow testing permissions'
        WF_DESCRIPTION = 'Testing Permissions'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]

        permissions = workflow.permissions
        self.assertEqual(len(permissions), len(_WF_PERMISSIONS))

        for permission in permissions:
            self.assertTrue(permission in _WF_PERMISSIONS)

    def test_from_empty_dcworkflow_workflow_variables(self):
        WF_ID = 'dcworkflow_variables'
        WF_TITLE = 'DC Workflow testing variables'
        WF_DESCRIPTION = 'Testing Variables'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]

        variables = workflow.variables

        self.assertEqual(len(variables.objectItems()), len(_WF_VARIABLES))

        for id, variable in variables.objectItems():

            expected = _WF_VARIABLES[variable.getId()]
            self.assertTrue(expected[0] in variable.description)
            self.assertEqual(variable.default_value, expected[1])
            self.assertEqual(variable.getDefaultExprText(), expected[2])
            self.assertEqual(variable.for_catalog, expected[3])
            self.assertEqual(variable.for_status, expected[4])
            self.assertEqual(variable.update_always, expected[5])

            guard = variable.getInfoGuard()

            self.assertEqual(guard.permissions, expected[6])
            self.assertEqual(guard.roles, expected[7])
            self.assertEqual(guard.groups, expected[8])
            self.assertEqual(guard.getExprText(), expected[9])

    def test_from_empty_dcworkflow_workflow_states(self):
        WF_ID = 'dcworkflow_states'
        WF_TITLE = 'DC Workflow testing states'
        WF_DESCRIPTION = 'Testing States'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]

        states = workflow.states

        self.assertEqual(len(states.objectItems()), len(_WF_STATES))

        for id, state in states.objectItems():
            expected = _WF_STATES[state.getId()]
            self.assertEqual(state.title, expected[0])
            self.assertTrue(expected[1] in state.description)

            self.assertEqual(len(state.transitions), len(expected[2]))

            for transition_id in state.transitions:
                self.assertTrue(transition_id in expected[2])

            for permission in state.getManagedPermissions():
                p_info = state.getPermissionInfo(permission)
                p_expected = expected[3].get(permission, [])

                self.assertEqual(bool(p_info['acquired']),
                                 isinstance(p_expected, list))

                self.assertEqual(len(p_info['roles']), len(p_expected))

                for role in p_info['roles']:
                    self.assertFalse(role not in p_expected)

            group_roles = state.group_roles or {}
            self.assertEqual(len(group_roles), len(expected[4]))

            for group_id, exp_roles in expected[4]:
                self.assertEqual(len(state.getGroupInfo(group_id)),
                                 len(exp_roles))
                for role in state.getGroupInfo(group_id):
                    self.assertTrue(role in exp_roles)

            self.assertEqual(len(state.getVariableValues()), len(expected[5]))

            for var_id, value in state.getVariableValues():
                self.assertEqual(value, expected[5][var_id])

    def test_from_empty_dcworkflow_workflow_transitions(self):
        WF_ID = 'dcworkflow_transitions'
        WF_TITLE = 'DC Workflow testing transitions'
        WF_DESCRIPTION = 'Testing Transitions'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]

        transitions = workflow.transitions

        self.assertEqual(len(transitions.objectItems()), len(_WF_TRANSITIONS))

        for id, transition in transitions.objectItems():
            expected = _WF_TRANSITIONS[transition.getId()]
            self.assertEqual(transition.title, expected[0])
            self.assertTrue(expected[1] in transition.description)
            self.assertEqual(transition.new_state_id, expected[2])
            self.assertEqual(transition.trigger_type, expected[3])
            self.assertEqual(transition.script_name, expected[4])
            self.assertEqual(transition.after_script_name, expected[5])
            self.assertEqual(transition.actbox_name, expected[6])
            self.assertEqual(transition.actbox_url, expected[7])
            self.assertEqual(transition.actbox_icon, expected[8])
            self.assertEqual(transition.actbox_category, expected[9])

            var_exprs = transition.var_exprs

            self.assertEqual(len(var_exprs), len(expected[10]))

            for var_id, expr in var_exprs.items():
                self.assertEqual(expr.text, expected[10][var_id])

            guard = transition.getGuard()

            self.assertEqual(guard.permissions, expected[11])
            self.assertEqual(guard.roles, expected[12])
            self.assertEqual(guard.groups, expected[13])
            self.assertEqual(guard.getExprText(), expected[14])

    def test_from_empty_dcworkflow_workflow_worklists(self):
        WF_ID = 'dcworkflow_worklists'
        WF_TITLE = 'DC Workflow testing worklists'
        WF_DESCRIPTION = 'Testing Worklists'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)

        workflow = tool.objectValues()[1]

        worklists = workflow.worklists

        self.assertEqual(len(worklists.objectItems()), len(_WF_WORKLISTS))

        for id, worklist in worklists.objectItems():
            expected = _WF_WORKLISTS[worklist.getId()]
            self.assertTrue(expected[1] in worklist.description)

            var_matches = worklist.var_matches

            self.assertEqual(len(var_matches), len(expected[2]))

            for var_id, values in var_matches.items():
                exp_values = expected[2][var_id]
                self.assertEqual(len(values), len(exp_values))

                for value in values:
                    self.assertTrue(value in exp_values, values)

            self.assertEqual(worklist.actbox_name, expected[3])
            self.assertEqual(worklist.actbox_url, expected[4])
            self.assertEqual(worklist.actbox_icon, expected[5])
            self.assertEqual(worklist.actbox_category, expected[6])

            guard = worklist.getGuard()

            self.assertEqual(guard.permissions, expected[7])
            self.assertEqual(guard.roles, expected[8])
            self.assertEqual(guard.groups, expected[9])
            self.assertEqual(guard.getExprText(), expected[10])

    def test_from_old_dcworkflow_workflow_scripts(self):
        WF_ID = 'old_dcworkflow_scripts'
        WF_TITLE = 'Old DC Workflow testing scripts'
        WF_INITIAL_STATE = 'closed'

        tool = self._importOldWorkflow(WF_ID, WF_TITLE, WF_INITIAL_STATE)
        workflow = tool.objectValues()[1]
        scripts = workflow.scripts

        self.assertEqual(len(scripts.objectItems()), len(_WF_SCRIPTS))

        for script_id, script in scripts.objectItems():
            expected = _WF_SCRIPTS[script_id]

            self.assertEqual(script.meta_type, expected[0])

            if script.meta_type == PythonScript.meta_type:
                self.assertEqual(script.manage_FTPget(), expected[1])

    def test_from_empty_dcworkflow_workflow_scripts(self):
        WF_ID = 'dcworkflow_scripts'
        WF_TITLE = 'DC Workflow testing scripts'
        WF_DESCRIPTION = 'Testing Scripts'
        WF_INITIAL_STATE = 'closed'

        tool = self._importNormalWorkflow(WF_ID, WF_TITLE, WF_DESCRIPTION,
                                          WF_INITIAL_STATE)
        workflow = tool.objectValues()[1]
        scripts = workflow.scripts

        self.assertEqual(len(scripts.objectItems()), len(_WF_SCRIPTS))

        for script_id, script in scripts.objectItems():

            expected = _WF_SCRIPTS[script_id]

            self.assertEqual(script.meta_type, expected[0])

            if script.meta_type == PythonScript.meta_type:
                self.assertEqual(script.manage_FTPget(), expected[1])

    def test_scripts_with_invalid_meta_type(self):
        """
        A script with an invalid meta_type should raise an error.

        Otherwise the previous script will be added for that script.
        """
        from Products.DCWorkflow import exportimport

        tool = self._importNormalWorkflow(
            'dcworkflow_scripts', 'DC Workflow testing scripts',
            'Testing Scripts', 'closed')
        workflow = tool.objectValues()[1]

        s_infos = [
            dict(script_id='invalid', meta_type='invalid',
                 filename='')]
        self.assertRaises(ValueError,
                          exportimport._initDCWorkflowScripts,
                          workflow, s_infos, None)

    def test_scripts_by_meta_type(self):
        """
        Constructors for meta_types other than those hard coded should
        be looked up.
        """
        from Products.DCWorkflow import exportimport

        tool = self._importNormalWorkflow(
            'dcworkflow_scripts', 'DC Workflow testing scripts',
            'Testing Scripts', 'closed')
        workflow = tool.objectValues()[1]
        scripts = workflow.scripts

        scripts.all_meta_types = scripts.all_meta_types() + [
            dict(instance=PythonScript, name='Foo Script')]

        s_infos = [
            dict(script_id='doc', meta_type='DTML Document',
                 filename=''),
            dict(script_id='bar', meta_type='Foo Script',
                 filename='')]
        exportimport._initDCWorkflowScripts(workflow, s_infos, None)

        self.assertEqual(scripts['doc'].meta_type, 'DTML Document')
        self.assertEqual(scripts['bar'].meta_type, 'Script (Python)')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WorkflowDefinitionConfiguratorTests),
        unittest.makeSuite(Test_exportWorkflow),
        unittest.makeSuite(Test_importWorkflow),
        ))
