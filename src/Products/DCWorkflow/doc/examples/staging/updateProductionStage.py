## Script (Python) "updateProductionStage"
##parameters=sci
# Copy the object in development to review and production.
object = sci.object
st = object.portal_staging
st.updateStages(object, 'dev', ['review', 'prod'],
                sci.kwargs.get('comment', ''))
