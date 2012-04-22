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
""" Guard tests.
"""

import unittest
import Testing

from AccessControl import getSecurityManager
from zope.component import getSiteManager
from zope.testing.cleanup import cleanUp

from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.WorkflowTool import WorkflowTool
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.Guard import Guard


class TestGuard(unittest.TestCase):

    def setUp(self):
        self.site = DummySite('site')

        # Construct a workflow
        self.wtool = WorkflowTool()
        self.wtool._setObject('wf', DCWorkflowDefinition('wf'))
        self.wtool.setDefaultChain('wf')
        sm = getSiteManager()
        sm.registerUtility(self.wtool, IWorkflowTool)
        sm.registerUtility(DummyTool(), ITypesTool)

    def tearDown(self):
        cleanUp()

    def _getDummyWorkflow(self):
        return self.wtool.wf

    def test_BaseGuardAPI(self):
        from zope.tales.tales import CompilerError

        #
        # Test guard basic API
        #

        guard = Guard()
        self.assertNotEqual(guard, None)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Initialize the guard with empty values
        # not initialization
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 0)

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager;',
                       'guard_permissions': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; ')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager;Member',
                       'guard_permissions': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager;Member',
                       'guard_permissions': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        # With one space after the ';'
        self.assertEqual(guard.getRolesText(), 'Manager; Member')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': 'ManagePortal;',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal; ')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': 'ManagePortal',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), '')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': 'ManagePortal',
                       'guard_expr': 'python:1'}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'python:1')

        # Change guard
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': 'ManagePortal',
                       'guard_expr': 'string:'}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 1)
        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # Change guard with wrong TALES
        guard_props = {'guard_roles': 'Manager',
                       'guard_permissions': 'ManagePortal',
                       'guard_expr': 'python:'}
        self.assertRaises(CompilerError,
                          guard.changeFromProperties, guard_props)

        self.assertEqual(guard.getRolesText(), 'Manager')
        self.assertEqual(guard.getPermissionsText(), 'ManagePortal')
        self.assertEqual(guard.getExprText(), 'string:')

        # reinit the guard
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': ''}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res == 0)

        # No API on DCWorkflow guard to reset properly....
        guard.permissions = ''
        guard.roles = ''
        guard.expr = None

        # Test default values
        self.assertEqual(guard.getPermissionsText(), '')
        self.assertEqual(guard.getRolesText(), '')
        self.assertEqual(guard.getExprText(), '')

        # XXX more tests with permissions and roles

    def test_checkGuardExpr(self):

        #
        # Basic checks.
        #

        guard = Guard()

        # Create compulsory context elements
        sm = getSecurityManager()
        self.site._setObject('dummy', DummyContent('dummy'))
        ob = self.site.dummy
        wf_def = self._getDummyWorkflow()

        # Initialize the guard with an ok guard
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': 'python:1'}

        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res)
        self.assertTrue(guard.check(sm, wf_def, ob))

        # Initialize the guard with a not ok guard
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': 'python:0'}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res)
        self.assertTrue(not guard.check(sm, wf_def, ob))

        # XXX more tests with permissions and roles

    def test_checkWithKwargs(self):

        #
        # Checks with kwargs
        #

        guard = Guard()

        # Create compulsory context elements
        sm = getSecurityManager()
        self.site._setObject('dummy', DummyContent('dummy'))
        ob = self.site.dummy
        wf_def = self._getDummyWorkflow()

        # Initialize the guard with an ok guard
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': 'python:1'}

        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res)
        self.assertTrue(guard.check(sm, wf_def, ob, arg1=1, arg2=2))

        # Initialize the guard with a not ok guard
        guard_props = {'guard_permissions': '',
                       'guard_roles': '',
                       'guard_expr': 'python:0'}
        res = guard.changeFromProperties(guard_props)
        self.assertTrue(res)
        self.assertTrue(not guard.check(sm, wf_def, ob, arg1=1, arg2=2))

        # XXX more tests with permissions and roles


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestGuard),
        ))
