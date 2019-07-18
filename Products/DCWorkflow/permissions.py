""" DCWorkflow product permissions
"""
from zope.deferredimport import deprecated


deprecated(
    'Please import from Products.CMFCore.permissions.',
    AccessContentsInformation=('Products.CMFCore.permissions:'
                               'AccessContentsInformation'),
    ManagePortal='Products.CMFCore.permissions:ManagePortal',
    ModifyPortalContent='Products.CMFCore.permissions:ModifyPortalContent',
    RequestReview='Products.CMFCore.permissions:RequestReview',
    ReviewPortalContent='Products.CMFCore.permissions:ReviewPortalContent',
    View='Products.CMFCore.permissions:View',
)
