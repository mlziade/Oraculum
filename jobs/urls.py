from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QueueJobViewSet

# DRF Router for jobs endpoints
router = DefaultRouter()
router.register(r'queue', QueueJobViewSet, basename='queue')

urlpatterns = [
    path('', include(router.urls)),
]