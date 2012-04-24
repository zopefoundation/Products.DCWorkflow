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
""" Scripts in a web-configurable workflow.
"""

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.Folder import Folder

from Products.DCWorkflow.ContainerTab import ContainerTab
from Products.DCWorkflow.permissions import ManagePortal


class Scripts(ContainerTab):
    """A container for workflow scripts"""

    meta_type = 'Workflow Scripts'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    def manage_main(self, client=None, REQUEST=None, **kw):
        '''
        '''
        kw['management_view'] = 'Scripts'
        m = Folder.manage_main.__of__(self)
        return m(self, client, REQUEST, **kw)

InitializeClass(Scripts)
