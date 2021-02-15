## Script (Python) "updateReviewStage"
##parameters=sci
# Copy the object in development to review.
object = sci.object
st = object.portal_staging
st.updateStages(object, 'dev', ['review'],
                sci.kwargs.get('comment', ''))
