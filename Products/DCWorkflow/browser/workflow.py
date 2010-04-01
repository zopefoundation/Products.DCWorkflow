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
"""DCWorkflowDefinition browser views.

$Id$
"""

from xml.dom.minidom import parseString

from zope.component import queryMultiAdapter
from zope.component import queryUtility

from Products.GenericSetup.browser.utils import AddWithPresettingsViewBase
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupTool

from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition


class DCWorkflowDefinitionAddView(AddWithPresettingsViewBase):

    """Add view for DCWorkflowDefinition.
    """

    klass = DCWorkflowDefinition

    description = u'Add a web-configurable workflow.'

    def getProfileInfos(self):
        profiles = []
        stool = queryUtility(ISetupTool)
        if stool:
            for info in stool.listContextInfos():
                obj_ids = []
                context = stool._getImportContext(info['id'])
                file_ids = context.listDirectory('workflows')
                for file_id in file_ids or ():
                    filename = 'workflows/%s/definition.xml' % file_id
                    body = context.readDataFile(filename)
                    if body is None:
                        continue
                    root = parseString(body).documentElement
                    obj_id = root.getAttribute('workflow_id')
                    obj_ids.append(obj_id)
                if not obj_ids:
                    continue
                obj_ids.sort()
                profiles.append({'id': info['id'],
                                 'title': info['title'],
                                 'obj_ids': tuple(obj_ids)})
        return tuple(profiles)

    def _initSettings(self, obj, profile_id, obj_path):
        stool = queryUtility(ISetupTool)
        if stool is None:
            return

        context = stool._getImportContext(profile_id)
        file_ids = context.listDirectory('workflows')
        for file_id in file_ids or ():
            filename = 'workflows/%s/definition.xml' % file_id
            body = context.readDataFile(filename)
            if body is None:
                continue

            root = parseString(body).documentElement
            if not root.getAttribute('workflow_id') == obj_path[0]:
                continue

            importer = queryMultiAdapter((obj, context), IBody)
            if importer is None:
                continue

            importer.body = body
            return
