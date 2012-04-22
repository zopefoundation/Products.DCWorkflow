##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for DCWorkflow module.
"""

import unittest
import Testing

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from zope.component import adapter
from zope.component import getSiteManager
from zope.component import provideHandler
from zope.interface.verify import verifyClass

from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IWorkflowTool
from Products.CMFCore.testing import TraversingEventZCMLLayer
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.tests.base.security import OmnipotentUser
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.WorkflowTool import WorkflowTool
from Products.DCWorkflow.interfaces import IAfterTransitionEvent
from Products.DCWorkflow.interfaces import IBeforeTransitionEvent


class DCWorkflowDefinitionTests(SecurityTest):

    layer = TraversingEventZCMLLayer

    def setUp(self):
        SecurityTest.setUp(self)
        self.app._setObject('site', DummySite('site'))
        self.site = self.app._getOb('site')
        self.wtool = self.site._setObject('portal_workflow', WorkflowTool())
        self._constructDummyWorkflow()
        transaction.savepoint(optimistic=True)
        newSecurityManager(None, OmnipotentUser().__of__(self.site))
        sm = getSiteManager()
        sm.registerUtility(self.wtool, IWorkflowTool)
        sm.registerUtility(DummyTool(), ITypesTool)

    def test_interfaces(self):
        from Products.CMFCore.interfaces import IWorkflowDefinition
        from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition

        verifyClass(IWorkflowDefinition, DCWorkflowDefinition)

    def _constructDummyWorkflow(self):
        from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition

        wtool = self.wtool
        wtool._setObject('wf', DCWorkflowDefinition('wf'))
        wtool.setDefaultChain('wf')
        wf = wtool.wf

        wf.states.addState('private')
        sdef = wf.states['private']
        sdef.setProperties(transitions=('publish',))

        wf.states.addState('published')
        wf.states.setInitialState('private')

        wf.transitions.addTransition('publish')
        tdef = wf.transitions['publish']
        tdef.setProperties(title='', new_state_id='published', actbox_name='')

        wf.variables.addVariable('comments')
        vdef = wf.variables['comments']
        vdef.setProperties(description='',
                 default_expr="python:state_change.kwargs.get('comment', '')",
                 for_status=1, update_always=1)

        wf.worklists.addWorklist('published_documents')

    def _getDummyWorkflow(self):
        return self.wtool.wf

    def test_doActionFor(self):
        wtool = self.wtool
        wf = self._getDummyWorkflow()

        dummy = self.site._setObject('dummy', DummyContent())
        wtool.notifyCreated(dummy)
        self.assertEqual(wf._getStatusOf(dummy),
                         {'state': 'private', 'comments': ''})
        wf.doActionFor(dummy, 'publish', comment='foo')
        self.assertEqual(wf._getStatusOf(dummy),
                         {'state': 'published', 'comments': 'foo'})

        # XXX more

    def test_events(self):
        events = []

        @adapter(IBeforeTransitionEvent)
        def _handleBefore(event):
            events.append(event)
        provideHandler(_handleBefore)

        @adapter(IAfterTransitionEvent)
        def _handleAfter(event):
            events.append(event)
        provideHandler(_handleAfter)

        wf = self._getDummyWorkflow()

        dummy = self.site._setObject('dummy', DummyContent())
        wf.doActionFor(dummy, 'publish', comment='foo', test='bar')

        self.assertEqual(4, len(events))

        evt = events[0]
        self.assertTrue(IBeforeTransitionEvent.providedBy(evt))
        self.assertEqual(dummy, evt.object)
        self.assertEqual('private', evt.old_state.id)
        self.assertEqual('private', evt.new_state.id)
        self.assertEqual(None, evt.transition)
        self.assertEqual({}, evt.status)
        self.assertEqual(None, evt.kwargs)

        evt = events[1]
        self.assertTrue(IAfterTransitionEvent.providedBy(evt))
        self.assertEqual(dummy, evt.object)
        self.assertEqual('private', evt.old_state.id)
        self.assertEqual('private', evt.new_state.id)
        self.assertEqual(None, evt.transition)
        self.assertEqual({'state': 'private', 'comments': ''}, evt.status)
        self.assertEqual(None, evt.kwargs)

        evt = events[2]
        self.assertTrue(IBeforeTransitionEvent.providedBy(evt))
        self.assertEqual(dummy, evt.object)
        self.assertEqual('private', evt.old_state.id)
        self.assertEqual('published', evt.new_state.id)
        self.assertEqual('publish', evt.transition.id)
        self.assertEqual({'state': 'private', 'comments': ''}, evt.status)
        self.assertEqual({'test': 'bar', 'comment': 'foo'}, evt.kwargs)

        evt = events[3]
        self.assertTrue(IAfterTransitionEvent.providedBy(evt))
        self.assertEqual(dummy, evt.object)
        self.assertEqual('private', evt.old_state.id)
        self.assertEqual('published', evt.new_state.id)
        self.assertEqual('publish', evt.transition.id)
        self.assertEqual({'state': 'published', 'comments': 'foo'}, evt.status)
        self.assertEqual({'test': 'bar', 'comment': 'foo'}, evt.kwargs)

    def test_checkTransitionGuard(self):
        wtool = self.wtool
        wf = self._getDummyWorkflow()
        dummy = self.site._setObject('dummy', DummyContent())
        wtool.notifyCreated(dummy)
        self.assertEqual(wf._getStatusOf(dummy),
                         {'state': 'private', 'comments': ''})

        # Check
        self.assertTrue(wf._checkTransitionGuard(wf.transitions['publish'],
                                                 dummy))

        # Check with kwargs propagation
        self.assertTrue(wf._checkTransitionGuard(wf.transitions['publish'],
                                                 dummy, arg1=1, arg2=2))

    def test_isActionSupported(self):
        wf = self._getDummyWorkflow()
        dummy = self.site._setObject('dummy', DummyContent())

        # check publish
        self.assertTrue(wf.isActionSupported(dummy, 'publish'))

        # Check with kwargs.
        self.assertTrue(wf.isActionSupported(dummy, 'publish', arg1=1, arg2=2))

    def test_rename(self):
        wf = self._getDummyWorkflow()

        wf.states.manage_renameObject('private', 'private_new')
        self.assertNotEqual(None, wf.states._getOb('private_new', None))

        wf.transitions.manage_renameObject('publish', 'publish_new')
        self.assertNotEqual(None, wf.transitions._getOb('publish_new', None))

        wf.variables.manage_renameObject('comments', 'comments_new')
        self.assertNotEqual(None, wf.variables._getOb('comments_new', None))

        wf.worklists.manage_renameObject('published_documents',
                                         'published_documents_new')
        self.assertNotEqual(None,
                          wf.worklists._getOb('published_documents_new', None))

    def test_worklists(self):
        wf = self._getDummyWorkflow()
        worklist = wf.worklists._getOb('published_documents')
        # check ZMI
        wf.worklists.manage_main(self.REQUEST)
        # store an Expression
        worklist.setProperties('', props={'var_match_state': 'string:private'})
        # check ZMI
        wf.worklists.manage_main(self.REQUEST)


    # XXX more tests...


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DCWorkflowDefinitionTests),
        ))
