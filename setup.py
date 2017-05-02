# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os

version = '2.3.0dev'


def _package_doc(name):
    filepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    with open(filepath, 'r') as f:
        return f.read()


_boundary = '\n' + ('-' * 60) + '\n\n'
long_description = (
    _package_doc('README.rst') +
    _boundary +
    _package_doc('CHANGES.rst') +
    _boundary +
    'Download\n========'
)

setup(
    name='Products.DCWorkflow',
    version=version,
    description='DCWorkflow product for the Zope Content Management Framework',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Plone',
        'Framework :: Zope2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    keywords='web application server zope zope2 cmf',
    author="Zope Foundation and Contributors",
    author_email="zope-cmf@zope.org",
    url="http://pypi.python.org/pypi/Products.DCWorkflow",
    license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
    packages=find_packages(),
    include_package_data=True,
    namespace_packages=['Products'],
    zip_safe=False,
    setup_requires=['eggtestinfo', ],
    install_requires=[
        'setuptools',
        'Zope2 >= 4.0a2',
        'Products.CMFCore',
        'Products.ExternalMethod',
        'Products.GenericSetup',
        'Products.PythonScripts',
        # packages below this line should be removed once CMFCore if fixed to
        # work with Zope 4
        'ZServer',
        'Products.ZCatalog',
        'docutils',
    ],
    tests_require=[
        'zope.testing >= 3.7.0',
        'zope.testrunner',
    ],
    extras_require={
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'pkginfo'
        ]
    },
    test_loader='zope.testrunner.eggsupport:SkipLayers',
    test_suite='Products.DCWorkflow.tests',
    entry_points="""
    [zope2.initialize]
    Products.DCWorkflow = Products.DCWorkflow:initialize
    [distutils.commands]
    ftest = zope.testrunner.eggsupport:ftest
    """,
)
