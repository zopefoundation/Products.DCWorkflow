""" DCWorkflow product permissions

$Id$
"""
from AccessControl import ModuleSecurityInfo

security = ModuleSecurityInfo('Products.DCWorkflow.permissions')

security.declarePublic('AccessContentsInformation')
from Products.CMFCore.permissions import AccessContentsInformation

security.declarePublic('ManagePortal')
from Products.CMFCore.permissions import ManagePortal

security.declarePublic('ModifyPortalContent')
from Products.CMFCore.permissions import ModifyPortalContent

security.declarePublic('RequestReview')
from Products.CMFCore.permissions import RequestReview

security.declarePublic('ReviewPortalContent')
from Products.CMFCore.permissions import ReviewPortalContent

security.declarePublic('View')
from Products.CMFCore.permissions import View
