import os

from setuptools import find_packages
from setuptools import setup


def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()


NAME = 'DCWorkflow'
here = os.path.abspath(os.path.dirname(__file__))
_boundary = '\n' + ('-' * 60) + '\n\n'
README = (_package_doc('README.rst') + _boundary + _package_doc('CHANGES.txt'))
DESC = 'DCWorkflow product for the Zope Content Management Framework'

setup(name='Products.%s' % NAME,
      version='2.5.0',
      description=DESC,
      long_description=README,
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Plone',
        'Framework :: Zope :: 4',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Zope Public License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        ],
      keywords='web application server zope zope2 cmf',
      author='Zope Foundation and Contributors',
      author_email='zope-cmf@zope.org',
      url='https://pypi.org/project/Products.DCWorkflow',
      project_urls={
        'Issue Tracker': ('https://github.com/zopefoundation/'
                          'Products.DCWorkflow/issues'),
        'Sources': 'https://github.com/zopefoundation/Products.DCWorkflow',
      },
      license='ZPL 2.1',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*',
      install_requires=[
        'setuptools',
        'six',
        'Zope >= 4.0b4',
        'Products.CMFCore >= 2.4.0',
        'Products.ExternalMethod',
        'Products.GenericSetup >= 2.0b1',
        'Products.PythonScripts',
        ],
      extras_require={
        'docs': ['Sphinx', 'repoze.sphinx.autointerface', 'pkginfo']
        },
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      [distutils.commands]
      ftest = zope.testrunner.eggsupport:ftest
      """ % (NAME, NAME),
      )
