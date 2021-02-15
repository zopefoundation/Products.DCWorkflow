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
""" Guard conditions in a web-configurable workflow.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Explicit
from Acquisition import aq_base
from App.special_dtml import DTMLFile
from Persistence import Persistent

from Products.CMFCore.Expression import Expression
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import _checkPermission

from .Expression import StateChangeInfo
from .Expression import createExprContext
from .utils import _dtmldir


try:
    from html import escape
except ImportError:
    from cgi import escape


class Guard(Persistent, Explicit):

    permissions = ()
    roles = ()
    groups = ()
    expr = None

    security = ClassSecurityInfo()
    security.declareObjectProtected(ManagePortal)

    guardForm = DTMLFile('guard', _dtmldir)

    def check(self, sm, wf_def, ob, **kw):
        """Checks conditions in this guard.
        """
        u_roles = None
        if wf_def.manager_bypass:
            # Possibly bypass.
            u_roles = sm.getUser().getRolesInContext(ob)
            if 'Manager' in u_roles:
                return 1
        if self.permissions:
            for p in self.permissions:
                if _checkPermission(p, ob):
                    break
            else:
                return 0
        if self.roles:
            # Require at least one of the given roles.
            if u_roles is None:
                u_roles = sm.getUser().getRolesInContext(ob)
            for role in self.roles:
                if role in u_roles:
                    break
            else:
                return 0
        if self.groups:
            # Require at least one of the specified groups.
            u = sm.getUser()
            b = aq_base(u)
            if hasattr(b, 'getGroupsInContext'):
                u_groups = u.getGroupsInContext(ob)
            elif hasattr(b, 'getGroups'):
                u_groups = u.getGroups()
            else:
                u_groups = ()
            for group in self.groups:
                if group in u_groups:
                    break
            else:
                return 0
        expr = self.expr
        if expr is not None:
            econtext = createExprContext(
                StateChangeInfo(ob, wf_def, kwargs=kw))
            res = expr(econtext)
            if not res:
                return 0
        return 1

    @security.protected(ManagePortal)
    def getSummary(self):
        # Perhaps ought to be in DTML.
        res = []
        if self.permissions:
            res.append('Requires permission:')
            res.append(formatNameUnion(self.permissions))
        if self.roles:
            if res:
                res.append('<br/>')
            res.append('Requires role:')
            res.append(formatNameUnion(self.roles))
        if self.groups:
            if res:
                res.append('<br/>')
            res.append('Requires group:')
            res.append(formatNameUnion(self.groups))
        if self.expr is not None:
            if res:
                res.append('<br/>')
            res.append('Requires expr:')
            res.append('<code>' + escape(self.expr.text) + '</code>')
        return ' '.join(res)

    def changeFromProperties(self, props):
        '''
        Returns 1 if changes were specified.
        '''
        if props is None:
            return 0
        res = 0
        s = props.get('guard_permissions', None)
        if s:
            res = 1
            p = [permission.strip() for permission in s.split(';')]
            self.permissions = tuple(p)
        s = props.get('guard_roles', None)
        if s:
            res = 1
            r = [role.strip() for role in s.split(';')]
            self.roles = tuple(r)
        s = props.get('guard_groups', None)
        if s:
            res = 1
            g = [group.strip() for group in s.split(';')]
            self.groups = tuple(g)
        s = props.get('guard_expr', None)
        if s:
            res = 1
            self.expr = Expression(s)
        return res

    @security.protected(ManagePortal)
    def getPermissionsText(self):
        if not self.permissions:
            return ''
        return '; '.join(self.permissions)

    @security.protected(ManagePortal)
    def getRolesText(self):
        if not self.roles:
            return ''
        return '; '.join(self.roles)

    @security.protected(ManagePortal)
    def getGroupsText(self):
        if not self.groups:
            return ''
        return '; '.join(self.groups)

    @security.protected(ManagePortal)
    def getExprText(self):
        if not self.expr:
            return ''
        return str(self.expr.text)


InitializeClass(Guard)


def formatNameUnion(names):
    escaped = ['<code>' + escape(name) + '</code>' for name in names]
    if len(escaped) == 2:
        return ' or '.join(escaped)
    elif len(escaped) > 2:
        escaped[-1] = ' or ' + escaped[-1]
    return '; '.join(escaped)
