from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadPictureViewSet, ProcessingQueueViewSet

# DRF Router for gallery endpoints
router = DefaultRouter()
router.register(r'pictures', UploadPictureViewSet, basename='pictures')
router.register(r'jobs', ProcessingQueueViewSet, basename='jobs')

urlpatterns = [
    path('', include(router.urls)),
]