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
""" A convenient base class for representing a container as a management tab.
"""

from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from OFS.Folder import Folder
from zExceptions import BadRequest

_marker = []  # Create a new marker object.


class ContainerTab(Folder):

    def __init__(self, id):
        self.id = id
        self._mapping = {}

    def getId(self):
        return self.id

    def manage_options(self):
        parent = aq_parent(aq_inner(self))
        res = []
        options = parent.manage_options
        if callable(options):
            options = options()
        for item in options:
            item = item.copy()
            item['action'] = '../' + item['action']
            res.append(item)
        return res

    def manage_workspace(self, RESPONSE):
        '''
        Redirects to the primary option.
        '''
        RESPONSE.redirect(self.absolute_url() + '/manage_main')

    def _checkId(self, id, allow_dup=0):
        if not allow_dup:
            if id in self._mapping:
                raise BadRequest('The id "%s" is already in use.' % id)
        return Folder._checkId(self, id, allow_dup)

    def _getOb(self, name, default=_marker):
        mapping = self._mapping
        if name in mapping:
            res = mapping[name]
            if hasattr(res, '__of__'):
                res = res.__of__(self)
            return res
        else:
            if default is _marker:
                raise KeyError(name)
            return default

    def __getattr__(self, name):
        ob = self._mapping.get(name, None)
        if ob is not None:
            return ob
        raise AttributeError(name)

    def _setOb(self, name, value):
        mapping = self._mapping
        mapping[name] = aq_base(value)
        self._mapping = mapping  # Trigger persistence.

    def _delOb(self, name):
        mapping = self._mapping
        del mapping[name]
        self._mapping = mapping  # Trigger persistence.

    def get(self, name, default=None):
        if name in self._mapping:
            return self[name]
        else:
            return default

    def has_key(self, key):
        return key in self._mapping

    def objectIds(self, spec=None):
        # spec is not important for now...
        return self._mapping.keys()

    def keys(self):
        return self._mapping.keys()

    def items(self):
        return map(lambda id, self=self: (id, self._getOb(id)),
                   self._mapping.keys())

    def values(self):
        return map(lambda id, self=self: self._getOb(id),
                   self._mapping.keys())

    def manage_renameObjects(self, ids=[], new_ids=[], REQUEST=None):
        """Rename several sub-objects"""
        if len(ids) != len(new_ids):
            raise BadRequest('Please rename each listed object.')
        for i in range(len(ids)):
            if ids[i] != new_ids[i]:
                self.manage_renameObject(ids[i], new_ids[i])
        if REQUEST is not None:
            return self.manage_main(REQUEST)
        return None
