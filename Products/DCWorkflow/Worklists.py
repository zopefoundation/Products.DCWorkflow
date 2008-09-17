##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from Globals import DTMLFile
from Globals import InitializeClass
from Globals import PersistentMapping
from OFS.SimpleItem import SimpleItem

from ContainerTab import ContainerTab
from Guard import Guard
from permissions import ManagePortal
from utils import _dtmldir


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

    manage_options = (
        {'label': 'Properties', 'action': 'manage_properties'},
        )

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
            if not isinstance(matches, tuple):
                # Old version, convert it.
                matches = (matches,)
                self.var_matches[id] = matches
            return matches
        else:
            return ()

    def getVarMatchText(self, id):
        values = self.getVarMatch(id)
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
                v = [ var.strip() for var in v.split(';') ]
                self.var_matches[key] = tuple(v)
            else:
                if self.var_matches and self.var_matches.has_key(key):
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

InitializeClass(WorklistDefinition)


class Worklists(ContainerTab):
    """A container for worklist definitions"""

    meta_type = 'Worklists'

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    all_meta_types = ({'name':WorklistDefinition.meta_type,
                       'action':'addWorklist',
                       },)

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
