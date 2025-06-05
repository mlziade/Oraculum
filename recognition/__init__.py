"""
Face recognition module for the Oraculum project.

This module provides face detection and extraction services using OpenCV.
"""

from .service import FaceExtractionService
from .detection_methods import FaceDetectionMethod

__all__ = ['FaceExtractionService', 'FaceDetectionMethod']
