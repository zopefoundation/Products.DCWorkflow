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
""" Worklists in a web-configurable workflow.
"""

import re

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from Persistence import PersistentMapping
from zope.component import getUtility

from Products.CMFCore.interfaces import ICatalogTool
from Products.DCWorkflow.ContainerTab import ContainerTab
from Products.DCWorkflow.Expression import createExprContext
from Products.DCWorkflow.Expression import Expression
from Products.DCWorkflow.Expression import StateChangeInfo
from Products.DCWorkflow.Guard import Guard
from Products.DCWorkflow.permissions import ManagePortal
from Products.DCWorkflow.utils import _dtmldir

tales_re = re.compile(r'(\w+:)?(.*)')


class WorklistDefinition(SimpleItem):

    """Worklist definiton"""

    meta_type = 'Worklist'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    description = ''
    var_matches = None  # Compared with catalog when set.
    actbox_name = ''
    actbox_url = ''
    actbox_icon = ''
    actbox_category = 'global'
    guard = None

    manage_options = ({'label': 'Properties', 'action': 'manage_properties'},)

    def __init__(self, id):
        self.id = id

    def getGuard(self):
        if self.guard is not None:
            return self.guard
        else:
            return Guard().__of__(self)  # Create a temporary guard.

    def getGuardSummary(self):
        res = None
        if self.guard is not None:
            res = self.guard.getSummary()
        return res

    def getWorkflow(self):
        return aq_parent(aq_inner(aq_parent(aq_inner(self))))

    def getAvailableCatalogVars(self):
        res = []
        res.append(self.getWorkflow().state_var)
        for id, vdef in self.getWorkflow().variables.items():
            if vdef.for_catalog:
                res.append(id)
        res.sort()
        return res

    def getVarMatchKeys(self):
        if self.var_matches:
            return self.var_matches.keys()
        else:
            return []

    def getVarMatch(self, id):
        if self.var_matches:
            matches = self.var_matches.get(id, ())
            if not isinstance(matches, (tuple, Expression)):
                # Old version, convert it.
                matches = (matches,)
                self.var_matches[id] = matches
            return matches
        else:
            return ()

    def getVarMatchText(self, id):
        values = self.getVarMatch(id)
        if isinstance(values, Expression):
            return values.text
        return '; '.join(values)

    _properties_form = DTMLFile('worklist_properties', _dtmldir)

    def manage_properties(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._properties_form(REQUEST,
                                     management_view='Properties',
                                     manage_tabs_message=manage_tabs_message,
                                     )

    def setProperties(self, description,
                      actbox_name='', actbox_url='', actbox_category='global',
                      actbox_icon='', props=None, REQUEST=None):
        '''
        '''
        if props is None:
            props = REQUEST
        self.description = str(description)
        for key in self.getAvailableCatalogVars():
            # Populate var_matches.
            fieldname = 'var_match_%s' % key
            v = props.get(fieldname, '')
            if v:
                if not self.var_matches:
                    self.var_matches = PersistentMapping()

                if tales_re.match(v).group(1):
                    # Found a TALES prefix
                    self.var_matches[key] = Expression(v)
                else:
                    # Falling back to formatted string
                    v = [ var.strip() for var in v.split(';') ]
                    self.var_matches[key] = tuple(v)

            else:
                if self.var_matches and key in self.var_matches:
                    del self.var_matches[key]
        self.actbox_name = str(actbox_name)
        self.actbox_url = str(actbox_url)
        self.actbox_category = str(actbox_category)
        self.actbox_icon = str(actbox_icon)
        g = Guard()
        if g.changeFromProperties(props or REQUEST):
            self.guard = g
        else:
            self.guard = None
        if REQUEST is not None:
            return self.manage_properties(REQUEST, 'Properties changed.')

    def search(self, info=None, **kw):
        """ Perform the search corresponding to this worklist

        Returns sequence of ZCatalog brains
        - info is a mapping for resolving formatted string variable references
        - additional keyword/value pairs may be used to restrict the query
        """
        if not self.var_matches:
            return

        if info is None:
            info = {}

        criteria = {}

        for key, values in self.var_matches.items():
            if isinstance(values, Expression):
                wf = self.getWorkflow()
                portal = wf._getPortalRoot()
                context = createExprContext(StateChangeInfo(portal, wf))
                criteria[key] = values(context)
            else:
                criteria[key] = [x % info for x in values]

        criteria.update(kw)

        ctool = getUtility(ICatalogTool)
        return ctool.searchResults(**criteria)


InitializeClass(WorklistDefinition)


class Worklists(ContainerTab):

    """A container for worklist definitions"""

    meta_type = 'Worklists'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    all_meta_types = ({'name': WorklistDefinition.meta_type,
                       'action': 'addWorklist',
                       'permission': ManagePortal},)

    _manage_worklists = DTMLFile('worklists', _dtmldir)

    def manage_main(self, REQUEST, manage_tabs_message=None):
        '''
        '''
        return self._manage_worklists(
            REQUEST,
            management_view='Worklists',
            manage_tabs_message=manage_tabs_message,
            )

    def addWorklist(self, id, REQUEST=None):
        '''
        '''
        qdef = WorklistDefinition(id)
        self._setObject(id, qdef)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Worklist added.')

    def deleteWorklists(self, ids, REQUEST=None):
        '''
        '''
        for id in ids:
            self._delObject(id)
        if REQUEST is not None:
            return self.manage_main(REQUEST, 'Worklist(s) removed.')

InitializeClass(Worklists)
