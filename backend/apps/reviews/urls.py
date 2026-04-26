from django.urls import path

from apps.reviews.views import MyBatchReviewAPIView, ReviewDimensionListAPIView


urlpatterns = [
    path("dimensions/", ReviewDimensionListAPIView.as_view(), name="review-dimensions"),
    path("batches/<uuid:batch_id>/my-review/", MyBatchReviewAPIView.as_view(), name="batch-review"),
]
