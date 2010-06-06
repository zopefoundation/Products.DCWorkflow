##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit test layers.

$Id$
"""

from Testing.ZopeTestCase.layer import ZopeLite
from zope.testing.cleanup import cleanUp

from Products.CMFCore.testing import _DUMMY_ZCML

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class ExportImportZCMLLayer(ZopeLite):

    @classmethod
    def setUp(cls):
        import Products.Five
        import Products.GenericSetup
        import Products.CMFCore
        import Products.CMFCore.exportimport
        import Products.DCWorkflow

        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('meta.zcml', Products.GenericSetup)
        zcml.load_config('configure.zcml', Products.Five)
        zcml.load_config('configure.zcml', Products.GenericSetup)
        zcml.load_config('tool.zcml', Products.CMFCore)
        zcml.load_config('configure.zcml', Products.CMFCore.exportimport)
        zcml.load_config('tool.zcml', Products.DCWorkflow)
        zcml.load_config('exportimport.zcml', Products.DCWorkflow)
        zcml.load_string(_DUMMY_ZCML)

    @classmethod
    def tearDown(cls):
        cleanUp()
