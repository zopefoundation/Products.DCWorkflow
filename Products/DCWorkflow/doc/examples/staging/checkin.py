## Script (Python) "checkin"
##parameters=sci
# Check in the object to a Zope version repository, disallowing changes.
object = sci.object
vt = object.portal_versions
if vt.isCheckedOut(object):
  vt.checkin(object, sci.kwargs.get('comment', ''))
