from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadPictureViewSet

# DRF Router for gallery endpoints
router = DefaultRouter()
router.register(r'pictures', UploadPictureViewSet, basename='pictures')

urlpatterns = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('', include(router.urls)),
]