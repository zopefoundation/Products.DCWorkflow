import os

from setuptools import setup


def _package_doc(name):
    f = open(os.path.join(here, name))
    return f.read()


NAME = 'DCWorkflow'
here = os.path.abspath(os.path.dirname(__file__))
_boundary = '\n' + ('-' * 60) + '\n\n'
README = (_package_doc('README.rst') + _boundary + _package_doc('CHANGES.rst'))
DESC = 'DCWorkflow product for the Zope Content Management Framework'

setup(name='Products.%s' % NAME,
      version='4.0',
      description=DESC,
      long_description=README,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Framework :: Plone',
          'Framework :: Zope :: 5',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Zope Public License',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
          'Programming Language :: Python :: 3.14',
          'Topic :: Software Development',
          'Topic :: Software Development :: Libraries'
          ' :: Application Frameworks',
      ],
      keywords='web application server zope cmf',
      author='Zope Foundation and Contributors',
      author_email='zope-dev@zope.dev',
      url='https://pypi.org/project/Products.DCWorkflow',
      project_urls={
          'Issue Tracker': ('https://github.com/zopefoundation/'
                            'Products.DCWorkflow/issues'),
          'Sources': 'https://github.com/zopefoundation/Products.DCWorkflow',
      },
      license='ZPL-2.1',
      python_requires='>=3.10',
      install_requires=[
          'Zope >= 5.0',
          'Products.CMFCore >= 2.4.0',
          'Products.ExternalMethod',
          'Products.GenericSetup >= 2.0b1',
          'Products.PythonScripts',
      ],
      extras_require={
          'docs': ['Sphinx', 'repoze.sphinx.autointerface', 'furo']
      },
      include_package_data=True,
      entry_points=f"""
      [zope2.initialize]
      Products.{NAME} = Products.{NAME}:initialize
      [distutils.commands]
      ftest = zope.testrunner.eggsupport:ftest
      """,
      )
