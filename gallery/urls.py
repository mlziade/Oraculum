from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadPictureViewSet, QueryingPicturesViewSet

# DRF Router for gallery endpoints
router = DefaultRouter()
router.register(r'pictures', UploadPictureViewSet, basename='pictures')
router.register(r'query', QueryingPicturesViewSet, basename='query')

urlpatterns = [
    path('', include(router.urls)),
]