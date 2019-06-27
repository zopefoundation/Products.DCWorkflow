import os
from setuptools import setup
from setuptools import find_packages

NAME = 'DCWorkflow'

here = os.path.abspath(os.path.dirname(__file__))

def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()

_boundary = '\n' + ('-' * 60) + '\n\n'
README = ( _package_doc('README.txt')
         + _boundary
         + _package_doc('CHANGES.txt')
         + _boundary
         + "Download\n========"
         )

setup(name='Products.%s' % NAME,
      version='2.4.0b3',
      description='DCWorkflow product for the Zope Content Management Framework',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope :: 2",
        "Framework :: Zope :: 4",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        ],
      keywords='web application server zope zope2 cmf',
      author="Zope Foundation and Contributors",
      author_email="zope-cmf@zope.org",
      url="https://pypi.org/project/Products.DCWorkflow",
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      setup_requires=['eggtestinfo',
                     ],
      install_requires=[
          'setuptools',
          'six',
          'Zope >= 4.0b4',
          'Products.CMFCore >= 2.4.0.dev0',
          'Products.ExternalMethod',
          'Products.GenericSetup >= 2.0b1',
          'Products.PythonScripts',
          ],
      tests_require=[
          'zope.testing >= 3.7.0',
          'zope.testrunner',
          ],
      extras_require={'docs':['Sphinx',
                             'repoze.sphinx.autointerface',
                             'pkginfo']
          },
      test_loader='zope.testrunner.eggsupport:SkipLayers',
      test_suite='Products.%s.tests' % NAME,
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      [distutils.commands]
      ftest = zope.testrunner.eggsupport:ftest
      """ % (NAME, NAME),
      )
