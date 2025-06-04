import cv2
import numpy as np
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FaceExtractionService:
    """Service for extracting faces from images using OpenCV"""
    
    def __init__(self):
        """Initialize the face extraction service with OpenCV cascade classifiers"""
        # Use OpenCV's built-in Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Optional: Add profile face cascade for better detection
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        if self.face_cascade.empty():
            raise Exception("Could not load frontal face cascade classifier")
        
        if self.profile_cascade.empty():
            logger.warning("Could not load profile face cascade classifier - only frontal faces will be detected")
            self.profile_cascade = None
    
    def extract_faces(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Extract faces from an image and return face detection information.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            List[Dict[str, Any]]: List of face detection results with bounding box and confidence info
        """
        try:
            # Validate image file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = []
            
            # Detect frontal faces
            frontal_faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Add frontal faces to results
            for (x, y, w, h) in frontal_faces:
                faces.append({
                    'bbox_x': int(x),
                    'bbox_y': int(y),
                    'bbox_width': int(w),
                    'bbox_height': int(h),
                    'confidence': self._calculate_confidence(gray, x, y, w, h),
                    'detection_type': 'frontal'
                })
            
            # Detect profile faces if cascade is available
            if self.profile_cascade is not None:
                profile_faces = self.profile_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Add profile faces to results (avoid duplicates)
                for (x, y, w, h) in profile_faces:
                    # Check if this face overlaps significantly with any existing face
                    if not self._is_duplicate_face(faces, x, y, w, h):
                        faces.append({
                            'bbox_x': int(x),
                            'bbox_y': int(y),
                            'bbox_width': int(w),
                            'bbox_height': int(h),
                            'confidence': self._calculate_confidence(gray, x, y, w, h),
                            'detection_type': 'profile'
                        })
            
            logger.info(f"Detected {len(faces)} faces in image: {image_path}")
            return faces
            
        except Exception as e:
            logger.error(f"Error extracting faces from {image_path}: {str(e)}")
            raise
    
    def _calculate_confidence(self, gray_image: np.ndarray, x: int, y: int, w: int, h: int) -> float:
        """
        Calculate a confidence score for the detected face.
        This is a simplified approach since Haar cascades don't provide confidence directly.
        
        Args:
            gray_image: Grayscale image
            x, y, w, h: Bounding box coordinates
            
        Returns:
            float: Confidence score between 0.0 and 1.0
        """
        try:
            # Extract face region
            face_region = gray_image[y:y+h, x:x+w]
            
            # Calculate metrics that might indicate face quality
            # 1. Size factor (larger faces tend to be more reliable)
            size_factor = min(1.0, (w * h) / (100 * 100))  # Normalize to 100x100 baseline
            
            # 2. Contrast factor (faces with good contrast are more reliable)
            contrast = np.std(face_region) / 255.0  # Normalize standard deviation
            
            # 3. Edge density (faces should have reasonable edge content)
            edges = cv2.Canny(face_region, 50, 150)
            edge_density = np.sum(edges > 0) / (w * h)
            
            # Combine factors into a confidence score
            confidence = (size_factor * 0.3 + 
                         min(contrast, 1.0) * 0.4 + 
                         min(edge_density * 10, 1.0) * 0.3)
            
            # Ensure confidence is between 0.5 and 1.0 for detected faces
            confidence = max(0.5, min(1.0, confidence))
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {str(e)}")
            return 0.7  # Default moderate confidence
    
    def _is_duplicate_face(self, existing_faces: List[Dict[str, Any]], x: int, y: int, w: int, h: int) -> bool:
        """
        Check if a detected face significantly overlaps with any existing face.
        
        Args:
            existing_faces: List of already detected faces
            x, y, w, h: Bounding box of the new face
            
        Returns:
            bool: True if this face is likely a duplicate
        """
        new_face_area = w * h
        
        for face in existing_faces:
            # Calculate intersection
            x1 = max(x, face['bbox_x'])
            y1 = max(y, face['bbox_y'])
            x2 = min(x + w, face['bbox_x'] + face['bbox_width'])
            y2 = min(y + h, face['bbox_y'] + face['bbox_height'])
            
            if x2 > x1 and y2 > y1:
                intersection_area = (x2 - x1) * (y2 - y1)
                existing_face_area = face['bbox_width'] * face['bbox_height']
                
                # Calculate overlap ratio
                overlap_ratio = intersection_area / min(new_face_area, existing_face_area)
                
                # If overlap is more than 50%, consider it a duplicate
                if overlap_ratio > 0.5:
                    return True
        
        return False
    
    def validate_image(self, image_path: str) -> bool:
        """
        Validate that an image can be processed for face extraction.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            bool: True if image is valid for processing
        """
        try:
            if not os.path.exists(image_path):
                return False
                
            image = cv2.imread(image_path)
            return image is not None
            
        except Exception:
            return False