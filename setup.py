import os
from setuptools import setup
from setuptools import find_packages

NAME = 'DCWorkflow'

here = os.path.abspath(os.path.dirname(__file__))
package = os.path.join(here, 'Products', NAME)

def _package_doc(name):
    f = open(os.path.join(package, name))
    return f.read()

VERSION = _package_doc('version.txt').strip()
if VERSION.startswith('CMF'):
    VERSION = VERSION[len('CMF'):]
if VERSION.startswith(NAME):
    VERSION = VERSION[len(NAME):]
while VERSION and VERSION[0] in '-_.':
    VERSION = VERSION[1:]

_boundary = '\n' + ('-' * 60) + '\n'
README = (open(os.path.join(here, 'README.txt')).read()
        + _boundary + _package_doc('README.txt')
         )

setup(name='Products.%s' % NAME,
      version=VERSION,
      description='DCWorkflow product for Zope Content Management Framework',
      long_description=README,
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Plone",
        "Framework :: Zope2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Zope Public License",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        ],
      keywords='web application server zope zope2 cmf',
      author="Zope Corporation and contributors",
      author_email="zope-cmf@lists.zope.org",
      url="http://www.zope.org/Products/%s" % NAME,
      license="ZPL 2.1 (http://www.zope.org/Resources/License/ZPL-2.1)",
      packages=find_packages(),
      include_package_data=True,
      namespace_packages=['Products'],
      zip_safe=False,
      install_requires=['setuptools',
                        'Products.CMFCore',
                       ],
      entry_points="""
      [zope2.initialize]
      Products.%s = Products.%s:initialize
      """ % (NAME, NAME),
      )
