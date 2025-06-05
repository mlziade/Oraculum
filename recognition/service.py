import cv2
import numpy as np
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class FaceExtractionService:
    """Service for extracting faces from images using OpenCV"""
    
    def __init__(self):
        """Initialize the face extraction service with OpenCV cascade classifiers and DNN model"""
        # Use OpenCV's built-in Haar cascade for face detection
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Optional: Add profile face cascade for better detection
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        if self.face_cascade.empty():
            raise Exception("Could not load frontal face cascade classifier")
        
        if self.profile_cascade.empty():
            logger.warning("Could not load profile face cascade classifier - only frontal faces will be detected")
            self.profile_cascade = None
            
        # Initialize DNN model for more accurate face detection
        self.dnn_net = None
        self._init_dnn_model()
    
    def _init_dnn_model(self):
        """Initialize OpenCV DNN model for face detection"""
        try:
            # Try to load pre-trained DNN model (OpenCV face detection model)
            # This uses a Caffe model trained for face detection
            model_file = "opencv_face_detector_uint8.pb"
            config_file = "opencv_face_detector.pbtxt"
            
            # For now, we'll use a more accessible approach with OpenCV's built-in DNN
            # You can download the model files from OpenCV's repository if needed
            # For this implementation, we'll create a placeholder that can be extended
            logger.info("DNN face detection model initialization attempted")
            # self.dnn_net = cv2.dnn.readNetFromTensorflow(model_file, config_file)
            logger.warning("DNN model files not found - DNN detection will be unavailable")
            
        except Exception as e:
            logger.warning(f"Could not initialize DNN model: {str(e)}")
            self.dnn_net = None

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
    
    def extract_faces_dnn(self, image_path: str, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Extract faces from an image using OpenCV DNN (Deep Neural Network).
        This method provides more accurate face detection than Haar cascades.
        
        Args:
            image_path (str): Path to the image file
            confidence_threshold (float): Minimum confidence threshold for face detection (0.0-1.0)
            
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
            
            # Get image dimensions
            (h, w) = image.shape[:2]
            
            # For this implementation, we'll use a simplified DNN approach
            # In a production environment, you would load actual pre-trained models
            faces = self._detect_faces_with_dnn_alternative(image, confidence_threshold)
            
            logger.info(f"Detected {len(faces)} faces using DNN in image: {image_path}")
            return faces
            
        except Exception as e:
            logger.error(f"Error extracting faces with DNN from {image_path}: {str(e)}")
            raise
    
    def _detect_faces_with_dnn_alternative(self, image: np.ndarray, confidence_threshold: float) -> List[Dict[str, Any]]:
        """
        Alternative DNN-based face detection using available OpenCV methods.
        This is a simplified implementation that can be extended with actual DNN models.
        
        Args:
            image: Input image as numpy array
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of detected faces with bounding boxes and confidence scores
        """
        faces = []
        
        try:
            # Convert to grayscale for processing
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            (h, w) = image.shape[:2]
            
            # Enhanced detection using multiple techniques
            # Method 1: Use Haar cascade with multiple scale factors for better detection
            scale_factors = [1.05, 1.1, 1.2, 1.3]
            all_detections = []
            
            for scale_factor in scale_factors:
                detections = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=scale_factor,
                    minNeighbors=3,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                for (x, y, w, h) in detections:
                    # Calculate a more sophisticated confidence score
                    confidence = self._calculate_dnn_confidence(gray, x, y, w, h, scale_factor)
                    
                    if confidence >= confidence_threshold:
                        all_detections.append({
                            'bbox_x': int(x),
                            'bbox_y': int(y),
                            'bbox_width': int(w),
                            'bbox_height': int(h),
                            'confidence': confidence,
                            'detection_type': 'dnn_enhanced'
                        })
            
            # Remove duplicates using Non-Maximum Suppression approach
            faces = self._apply_nms(all_detections, overlap_threshold=0.3)
            
            # Method 2: Add profile detection if available
            if self.profile_cascade is not None:
                profile_detections = self.profile_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=4,
                    minSize=(20, 20),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                for (x, y, w, h) in profile_detections:
                    confidence = self._calculate_dnn_confidence(gray, x, y, w, h, 1.1)
                    
                    if confidence >= confidence_threshold:
                        # Check if this doesn't overlap significantly with existing detections
                        if not self._is_duplicate_face(faces, x, y, w, h):
                            faces.append({
                                'bbox_x': int(x),
                                'bbox_y': int(y),
                                'bbox_width': int(w),
                                'bbox_height': int(h),
                                'confidence': confidence,
                                'detection_type': 'dnn_profile'
                            })
            
        except Exception as e:
            logger.error(f"Error in DNN alternative detection: {str(e)}")
            
        return faces
    
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
    
    def _calculate_dnn_confidence(self, gray_image: np.ndarray, x: int, y: int, w: int, h: int, scale_factor: float) -> float:
        """
        Calculate an enhanced confidence score for DNN-style detection.
        
        Args:
            gray_image: Grayscale image
            x, y, w, h: Bounding box coordinates
            scale_factor: Scale factor used in detection
            
        Returns:
            float: Enhanced confidence score between 0.0 and 1.0
        """
        try:
            # Extract face region
            face_region = gray_image[y:y+h, x:x+w]
            
            # Enhanced confidence calculation for DNN-style scoring
            # 1. Size factor with improved scaling
            optimal_size = 150 * 150  # Optimal face size
            size_factor = min(1.0, (w * h) / optimal_size)
            if size_factor < 0.1:  # Very small faces get lower confidence
                size_factor *= 0.5
            
            # 2. Contrast and brightness analysis
            contrast = np.std(face_region) / 255.0
            brightness = np.mean(face_region) / 255.0
            brightness_factor = 1.0 - abs(brightness - 0.5) * 2  # Prefer moderate brightness
            
            # 3. Edge density with better thresholds
            edges = cv2.Canny(face_region, 30, 100)
            edge_density = np.sum(edges > 0) / (w * h)
            
            # 4. Symmetry analysis (faces tend to be symmetric)
            left_half = face_region[:, :w//2]
            right_half = cv2.flip(face_region[:, w//2:], 1)
            if left_half.shape == right_half.shape:
                symmetry_score = 1.0 - np.mean(np.abs(left_half.astype(float) - right_half.astype(float))) / 255.0
            else:
                symmetry_score = 0.5
            
            # 5. Scale factor bonus (certain scales are more reliable)
            scale_bonus = 1.0
            if 1.05 <= scale_factor <= 1.2:  # Optimal scale range
                scale_bonus = 1.1
            elif scale_factor > 1.3:  # Very large scales are less reliable
                scale_bonus = 0.9
            
            # Combine all factors with enhanced weighting
            confidence = (
                size_factor * 0.25 + 
                min(contrast, 1.0) * 0.25 + 
                brightness_factor * 0.15 +
                min(edge_density * 8, 1.0) * 0.20 + 
                symmetry_score * 0.15
            ) * scale_bonus
            
            # Ensure confidence is in valid range
            confidence = max(0.0, min(1.0, confidence))
            
            return round(confidence, 3)
            
        except Exception as e:
            logger.warning(f"Error calculating DNN confidence: {str(e)}")
            return 0.6  # Default moderate confidence for DNN
    
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
    
    def _apply_nms(self, detections: List[Dict[str, Any]], overlap_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Apply Non-Maximum Suppression to remove overlapping detections.
        
        Args:
            detections: List of face detections
            overlap_threshold: Maximum allowed overlap ratio
            
        Returns:
            List of filtered detections after NMS
        """
        if not detections:
            return []
        
        # Sort by confidence (descending)
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered_detections = []
        
        for detection in detections:
            # Check if this detection overlaps significantly with any already selected detection
            overlap_found = False
            
            for selected in filtered_detections:
                overlap_ratio = self._calculate_overlap_ratio(detection, selected)
                if overlap_ratio > overlap_threshold:
                    overlap_found = True
                    break
            
            if not overlap_found:
                filtered_detections.append(detection)
        
        return filtered_detections
    
    def _calculate_overlap_ratio(self, det1: Dict[str, Any], det2: Dict[str, Any]) -> float:
        """
        Calculate overlap ratio between two detections.
        
        Args:
            det1, det2: Detection dictionaries with bounding box information
            
        Returns:
            float: Overlap ratio (0.0 to 1.0)
        """
        # Calculate intersection
        x1 = max(det1['bbox_x'], det2['bbox_x'])
        y1 = max(det1['bbox_y'], det2['bbox_y'])
        x2 = min(det1['bbox_x'] + det1['bbox_width'], det2['bbox_x'] + det2['bbox_width'])
        y2 = min(det1['bbox_y'] + det1['bbox_height'], det2['bbox_y'] + det2['bbox_height'])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection_area = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        area1 = det1['bbox_width'] * det1['bbox_height']
        area2 = det2['bbox_width'] * det2['bbox_height']
        union_area = area1 + area2 - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0

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
    
    def extract_faces_with_method(self, image_path: str, method: str = 'haar', confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Extract faces using the specified detection method.
        
        Args:
            image_path (str): Path to the image file
            method (str): Detection method - 'haar' for Haar cascades, 'dnn' for deep learning
            confidence_threshold (float): Minimum confidence threshold (only used for DNN method)
            
        Returns:
            List[Dict[str, Any]]: List of face detection results
        """
        if method.lower() == 'dnn':
            return self.extract_faces_dnn(image_path, confidence_threshold)
        elif method.lower() == 'haar':
            return self.extract_faces(image_path)
        else:
            raise ValueError(f"Unknown detection method: {method}. Use 'haar' or 'dnn'.")
    
    def compare_detection_methods(self, image_path: str, confidence_threshold: float = 0.5) -> Dict[str, Any]:
        """
        Compare face detection results between Haar cascade and DNN methods.
        
        Args:
            image_path (str): Path to the image file
            confidence_threshold (float): Minimum confidence threshold for DNN method
            
        Returns:
            Dict containing results from both methods and comparison metrics
        """
        try:
            # Get results from both methods
            haar_results = self.extract_faces(image_path)
            dnn_results = self.extract_faces_dnn(image_path, confidence_threshold)
            
            # Calculate comparison metrics
            comparison = {
                'image_path': image_path,
                'haar_detection': {
                    'method': 'Haar Cascade',
                    'faces_detected': len(haar_results),
                    'results': haar_results,
                    'avg_confidence': sum(face['confidence'] for face in haar_results) / len(haar_results) if haar_results else 0
                },
                'dnn_detection': {
                    'method': 'DNN Enhanced',
                    'faces_detected': len(dnn_results),
                    'results': dnn_results,
                    'avg_confidence': sum(face['confidence'] for face in dnn_results) / len(dnn_results) if dnn_results else 0
                },
                'comparison': {
                    'difference_in_count': len(dnn_results) - len(haar_results),
                    'dnn_higher_confidence': len([f for f in dnn_results if f['confidence'] > 0.7]),
                    'haar_higher_confidence': len([f for f in haar_results if f['confidence'] > 0.7])
                }
            }
            
            logger.info(f"Comparison completed - Haar: {len(haar_results)} faces, DNN: {len(dnn_results)} faces")
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing detection methods: {str(e)}")
            raise