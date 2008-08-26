## Script (Python) "checkout"
##parameters=sci
# Check out the object from a repository, allowing changes.
#
# For workflows that control staging, it makes sense to call this script
# before all transitions.
object = sci.object
vt = object.portal_versions
if not vt.isCheckedOut(object):
  vt.checkout(object)
