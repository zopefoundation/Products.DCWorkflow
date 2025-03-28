Products.DCWorkflow Changelog
=============================

3.1 (unreleased)
----------------

- Add support for Python 3.13.

- Drop support for Python 3.8.

- Add support for Python 3.12.

- Drop support for Python 3.7.

3.0 (2023-02-02)
----------------

- Drop support for Python 2.7, 3.5, 3.6.


2.7.0 (2022-12-16)
------------------

- Fix insidious buildout configuration bug for tests against Zope 4.

- Add support for Python 3.11.


2.6.0 (2022-07-12)
------------------

New features:

- Add support for Python 3.10.


2.5.0 (2021-04-26)
------------------

New features:

- Add support for Python 3.9.

Bug fixes:

- Avoid a deprecation warning when importing ``gather_permissions``
  (`#20 <https://github.com/zopefoundation/Products.DCWorkflow/issues/20>`_)

- Avoid a TypeError when adding a managed group to a workflow
  (`#18 <https://github.com/zopefoundation/Products.DCWorkflow/issues/18>`_)


2.4.1 (2020-03-09)
------------------

- Added compatibility with Zope 5 by not registering for the help system.


2.4.0 (2019-07-19)
------------------

- full flake8 code cleanup


2.4.0b3 (2019-06-27)
--------------------

- Add support for Python 3.8.

- Fix import of scripts.


2.4.0b2 (2018-11-07)
--------------------

- Prepare for Python 2 / 3 compatibility

- Import permissions directly from CMFCore and deprecate the
  permissions module in Products.DCWorkflow

- Use decorators for ZCA and to declare security.


2.4.0b1 (2017-05-04)
--------------------

- Target use with Zope 4: no longer support 2.13.x.


2.3.0 (2017-05-04)
------------------

- Export / import workflow-managed groups.


2.3.0-beta (2012-03-21)
-----------------------

- Removed string exceptions.
  (https://bugs.launchpad.net/zope-cmf/+bug/952301)

- Made sure converted tools are used as utilities.

- StateChangeInfo: Removed support for deprecated '_isPortalRoot' marker.

- Hardened XML import parsing against missing boolean attributes.
  (https://bugs.launchpad.net/zope-cmf/+bug/707927)

- Ensured that emitted XML export has a valid encoding, even when passed
  'None'.  (https://bugs.launchpad.net/zope-cmf/+bug/707927)

- Change default encoding of exports from None to utf-8.

- Require at least Zope 2.13.12.


2.2.4 (2011-11-01)
------------------

- Fixed issue with non-ascii chars in workflow definitions

- Don't crash worklist's ``manage_main`` if variables are Expression objects.
  (https://bugs.launchpad.net/zope-cmf/+bug/731394)

- Allow renaming of states, transitions, variables and worklists


2.2.3 (2011-01-12)
------------------

- Explicitly include permissions from CMFCore, which are needed now that
  they aren't declared in Five in Zope 2.13.


2.2.2 (2010-11-11)
------------------

- Fixed Chameleon compatibility in `state_groups.pt`.

- Workflow states cannot be renamed through the ZMI.
  (https://bugs.launchpad.net/zope-cmf/+bug/625722)


2.2.1 (2010-07-04)
------------------

- Deal with deprecation warnings for Zope 2.13.


2.2.0 (2010-01-04)
------------------

- no changes from version 2.2.0-beta


2.2.0-beta (2009-12-06)
-----------------------

- no changes from version 2.2.0-alpha


2.2.0-alpha (2009-11-13)
------------------------

- moved the Zope dependency to version 2.12.0b3dev

- Worklists: The catalog variable match setting can now be a
  formatted string (as before), but also a qualified TAL
  expression, meaning it has a prefix like "string:", "python:".
  (https://bugs.launchpad.net/zope-cmf/+bug/378292)

- exportimport: Support for instance creation guards and manager
  bypass added.
  (https://bugs.launchpad.net/zope-cmf/+bug/308947)

- Cleaned up / normalized imports:

  o Don't import from Globals;  instead, use real locations.

  o Make other imports use the actual source module, rather than an
    intermediate (e.g., prefer importing 'ClassSecurityInfo' from
    'AccessControl.SecurityInfo' rather than from 'AccessControl').

  o Avoid relative imports, which will break in later versions of Python.

- Strip trailing newlines in order to properly match with a msgid when
  translating transition descriptions.

- Workflow UI: Remove ancient cruft to accommodate the proprietary
  (and long dead) base_cms product.

- Worklists and Transitions: Add icon expression properties to worklist
  and transition actions and their GenericSetup profiles.

- Fixed an import error (Products.PageTemplates.TALES is gone on
  Zope trunk).  Because we require Zope >= 2.10, we don't need a
  BBB conditional import.


2.1.2 (2008-09-13)
------------------

- test fixture: Fix failng tests with GenericSetup > 1.3 by explicitly
  loading GS' meta.zcml during setup.


2.1.2-beta (2008-08-26)
-----------------------

- completed devolution from monolithic CMF package into its component
  products that are distributed as eggs from PyPI.


2.1.1 (2008-01-06)
------------------

- no changes


2.1.1-beta(2007-12/29)
----------------------

- Testing: Derive test layers from ZopeLite layer if available.

- exportimport: Scripts with invalid types imported
  after scripts with valid types will no longer place the valid
  script twice.  Scripts can also now be specified with meta_types
  other than the hard-coded meta_types.

- AfterTransitionEvent now passes along the new status of the
  object, just as StateChangeInfo passes on the new status to
  after-transition scripts.
  (http://www.zope.org/Collectors/CMF/490)


2.1.0 (2007-08-08)
------------------

- Fixed all componentregistry.xml files to use plain object paths and strip
  and slashes. GenericSetup does only support registering objects which are
  in the site root.


2.1.0-beta2 (2007-07-12)
------------------------

- moved the Zope dependency to version 2.10.4

- Remove antique usage of marker attributes in favor of interfaces,
  leaving BBB behind for places potentially affecting third-party code.
  (http://www.zope.org/Collectors/CMF/440)

- Add POST-only protections to security critical methods.
  http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2007-0240)

- Workflow definition instances now have a description field
  (http://www.zope.org/Collectors/CMF/480)


2.1.0-beta (2007-03-09)
-----------------------

- moved the Zope dependency to verson 2.10.2

- Tool lookup and registration is now done "the Zope 3 way" as utilities, see
  http://svn.zope.org/CMF/branches/2.1/docs/ToolsAreUtilities.stx?view=auto

- Merged patches from Martin Aspeli to enable generating events before
  and after DCWorkflow transitions, and in the 'notify' methods of the
  workflow tool (http://www.zope.org/Collectors/CMF/461).


2.1.0-alpha2 (2006-11-23)
-------------------------

- moved the Zope dependency to version 2.10.1

- Fixed test breakage induced by use of Z3 pagetemplates in Zope 2.10+.

- browser views: Added some zope.formlib based forms.

- testing: Added test layers for setting up ZCML.


2.1.0-alpha (2006-10-09)
------------------------

- skins: Changed encoding of translated portal_status_messages.
  Now getBrowserCharset is used to play nice with Five forms. Customized
  setRedirect and getMainGlobals scripts have to be updated.

- Profiles: All profiles are now registered by ZCML.

- ZClasses: Removed unmaintained support for ZClasses.
  Marked the 'initializeBases*' methods as deprecated.

- Content: Added IFactory utilities for all content classes.
  They are now used by default instead of the old constructor methods.

- Content: All content classes are now registered by ZCML.
  ContentInit is still used to register oldstyle constructors.

- setup handlers: Removed support for CMF 1.5 CMFSetup profiles.


Earlier releases
----------------

For a complete list of changes before version 2.1.0-alpha, see the HISTORY.txt
file on the CMF-2.1 branch:
http://svn.zope.org/CMF/branches/2.1/HISTORY.txt?view=auto
