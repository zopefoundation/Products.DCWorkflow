## Script (Python) "retractStages"
##parameters=sci
# Remove the object from the given stages.
object = sci.object
st = object.portal_staging
st.removeStages(object, ['review', 'prod'])
