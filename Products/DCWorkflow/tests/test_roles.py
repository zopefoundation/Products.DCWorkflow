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
""" Unit tests of role-mapping machinery.
"""

import unittest
import Testing

from OFS.Folder import Folder
from OFS.Application import Application
from Products.DCWorkflow.utils \
     import modifyRolesForPermission, modifyRolesForGroup


class RoleMapTests(unittest.TestCase):

    def setUp(self):
        self.app = Application()
        self.app.ob = Folder()
        self.ob = self.app.ob
        self.ob.__ac_local_roles__ = {
            '(Group) Administrators': ['Manager', 'Member'],
            '(Group) Users': ['Member'],
            }
        self.ob._View_Permission = ('Member', 'Manager')
        self.ob._View_management_screens_Permission = ('Manager',)

    def testModifyRolesForGroup(self):
        modifyRolesForGroup(
            self.ob, '(Group) Administrators', ['Owner'], ['Member', 'Owner'])
        modifyRolesForGroup(
            self.ob, '(Group) Users', [], ['Member'])
        self.assertEqual(self.ob.__ac_local_roles__, {
            '(Group) Administrators': ['Manager', 'Owner'],
            })
        modifyRolesForGroup(
            self.ob, '(Group) Administrators', ['Member'], ['Member', 'Owner'])
        modifyRolesForGroup(
            self.ob, '(Group) Users', ['Member'], ['Member'])
        self.assertEqual(self.ob.__ac_local_roles__, {
            '(Group) Administrators': ['Manager', 'Member'],
            '(Group) Users': ['Member'],
            })

    def testModifyRolesForPermission(self):
        modifyRolesForPermission(self.ob, 'View', ['Manager'])
        modifyRolesForPermission(
            self.ob, 'View management screens', ['Member'])
        self.assertEqual(self.ob._View_Permission, ['Manager'])
        self.assertEqual(
            self.ob._View_management_screens_Permission, ['Member'])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(RoleMapTests),
        ))
