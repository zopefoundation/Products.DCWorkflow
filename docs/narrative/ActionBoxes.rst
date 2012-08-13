Action Boxes
============

Action box settings are required for work lists and any transition that is
intended to be a user initiated action. They define how the action will
appear in the action box, what section it will appear in and what it will
link to.

Names and URLs for the actions box can be formatted using standard Python
string formatting. An example::

  %(object_url)s/content_submit_form

The string '%(object_url)s' will be replaced by the value of object_url.
The following names are available:

* portal_url

* folder_url

* object_url

* count (Available in work lists only. Represents the number of items in the
  work list.)

The following names are also available, in case there is any use for them.
They are not strings.

* portal

* folder

* object

* isAnonymous

Note that this formatting is done using standard Python string formatting
rather than TALES. It might be more appropriate to use TALES instead. As
always, patches welcome.
