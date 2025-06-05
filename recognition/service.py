import cv2
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)


class FaceExtractionService:
    """Service for extracting faces from images using OpenCV"""
    
    class DetectionMethodChoices:
        HAAR = 'haar', 'Haar Cascade'
        DNN = 'dnn', 'Deep Neural Network'
        
        @classmethod
        def choices(cls):
            return [cls.HAAR, cls.DNN]
    
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
            # Get the current directory and construct model paths
            current_dir = os.path.dirname(os.path.abspath(__file__))
            models_dir = os.path.join(current_dir, "models")
            
            model_file = os.path.join(models_dir, "opencv_face_detector_uint8.pb")
            config_file = os.path.join(models_dir, "opencv_face_detector.pbtxt")
            
            # Check if model files exist - log warning if missing but don't throw exception
            if not os.path.exists(model_file) or not os.path.exists(config_file):
                logger.warning("DNN model files not found - DNN detection will not be available")
                self.dnn_net = None
                return
            
            # Load the DNN model
            self.dnn_net = cv2.dnn.readNetFromTensorflow(model_file, config_file)
            
            if self.dnn_net.empty():
                logger.warning("Failed to load DNN model - DNN detection will not be available")
                self.dnn_net = None
            else:
                logger.info("DNN face detection model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Could not initialize DNN model: {str(e)} - DNN detection will not be available")
            self.dnn_net = None

    def extract_faces_haar(self, image_path: str) -> list[dict[str, any]]:
        """
        Extract faces from an image using Haar cascade classifiers and return face detection information.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list[dict[str, any]]: List of face detection results with bounding box and confidence info
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
                    'confidence': self._calculate_haar_confidence(gray, x, y, w, h),
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
                            'confidence': self._calculate_haar_confidence(gray, x, y, w, h),
                            'detection_type': 'profile'
                        })
            
            logger.info(f"Detected {len(faces)} faces in image: {image_path}")
            return faces
            
        except Exception as e:
            logger.error(f"Error extracting faces from {image_path}: {str(e)}")
            raise
    
    def extract_faces_dnn(self, image_path: str, confidence_threshold: float = 0.5) -> list[dict[str, any]]:
        """
        Extract faces from an image using OpenCV DNN (Deep Neural Network).
        This method provides more accurate face detection than Haar cascades.
        
        Args:
            image_path (str): Path to the image file
            confidence_threshold (float): Minimum confidence threshold for face detection (0.0-1.0)
            
        Returns:
            list[dict[str, any]]: List of face detection results with bounding box and confidence info
            
        Raises:
            Exception: If DNN model is not available
        """
        if self.dnn_net is None:
            raise Exception("DNN model is not available. Please ensure model files are present in the models directory.")
        
        try:
            # Validate image file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            faces = self._detect_faces_with_dnn(image, confidence_threshold)
            
            logger.info(f"Detected {len(faces)} faces using DNN in image: {image_path}")
            return faces
            
        except Exception as e:
            logger.error(f"Error extracting faces with DNN from {image_path}: {str(e)}")
            raise

    def _detect_faces_with_dnn(self, image: np.ndarray, confidence_threshold: float) -> list[dict[str, any]]:
        """
        Use OpenCV DNN model for face detection.
        
        Args:
            image: Input image as numpy array
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            List of detected faces with bounding boxes and confidence scores
        """
        faces = []
        
        try:
            (h, w) = image.shape[:2]
            
            # Create blob from image
            # The OpenCV face detector expects input size of 300x300
            blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123])
            
            # Set the blob as input to the network
            self.dnn_net.setInput(blob)
            
            # Run forward pass to get detections
            detections = self.dnn_net.forward()
            
            # Loop through the detections
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                # Filter weak detections
                if confidence > confidence_threshold:
                    # Get bounding box coordinates
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x, y, x1, y1) = box.astype("int")
                    
                    # Ensure coordinates are within image bounds
                    x = max(0, x)
                    y = max(0, y)
                    x1 = min(w, x1)
                    y1 = min(h, y1)
                    
                    # Calculate width and height
                    width = x1 - x
                    height = y1 - y
                    
                    # Only add valid detections
                    if width > 0 and height > 0:
                        faces.append({
                            'bbox_x': int(x),
                            'bbox_y': int(y),
                            'bbox_width': int(width),
                            'bbox_height': int(height),
                            'confidence': round(float(confidence), 3),
                            'detection_type': 'dnn'
                        })
            
            logger.info(f"DNN detected {len(faces)} faces with confidence > {confidence_threshold}")
            
        except Exception as e:
            logger.error(f"Error in DNN detection: {str(e)}")
            raise
            
        return faces
    
    def _calculate_haar_confidence(self, gray_image: np.ndarray, x: int, y: int, w: int, h: int) -> float:
        """
        Calculate a confidence score for the detected face using Haar cascade metrics.
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
            logger.warning(f"Error calculating Haar confidence: {str(e)}")
            return 0.7  # Default moderate confidence

    def _is_duplicate_face(self, existing_faces: list[dict[str, any]], x: int, y: int, w: int, h: int) -> bool:
        """
        Check if a detected face significantly overlaps with any existing face.
        
        Args:
            existing_faces: List of already detected faces
            x, y, w, h: Bounding box of the new face
            
        Returns:
            bool: True if this face is likely a duplicate
        """
        threshold = 0.3  # 30% overlap threshold
        
        for face in existing_faces:
            # Calculate intersection over union (IoU)
            i_x = max(face['bbox_x'], x)
            i_y = max(face['bbox_y'], y)
            i_x1 = min(face['bbox_x'] + face['bbox_width'], x + w)
            i_y1 = min(face['bbox_y'] + face['bbox_height'], y + h)
            
            # Calculate intersection area
            intersection = max(0, i_x1 - i_x) * max(0, i_y1 - i_y)
            
            # Calculate union area
            union = (face['bbox_width'] * face['bbox_height']) + (w * h) - intersection
            
            # Calculate IoU
            iou = intersection / union if union > 0 else 0
            
            # Check if IoU exceeds the threshold
            if iou > threshold:
                return True  # Duplicate face detected
        
        return False  # No significant overlap with existing faces

    def validate_image(self, image_path: str) -> bool:
        """
        Validate if the image at the given path is a valid image file and can be read by OpenCV.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            bool: True if image is valid and readable, False otherwise
        """
        try:
            # Attempt to open the image file
            image = cv2.imread(image_path)
            
            # If image is None, it means OpenCV could not read the file
            if image is None:
                logger.warning(f"Invalid image file (cannot be read): {image_path}")
                return False
            
            return True
        
        except Exception as e:
            logger.warning(f"Error validating image file {image_path}: {str(e)}")
            return False

    def extract_faces_with_method(self, image_path: str, method: str, confidence_threshold: float = 0.5) -> list[dict[str, any]]:
        """
        Extract faces using the specified detection method.
        
        Args:
            image_path (str): Path to the image file
            method (str): Detection method - use DetectionMethodChoices values (required)
            confidence_threshold (float): Minimum confidence threshold (only used for DNN method)
            
        Returns:
            list[dict[str, any]]: List of face detection results
            
        Raises:
            ValueError: If method is None, empty, or not a valid detection method
            Exception: If DNN method is requested but model is not available
        """
        # Check if method is provided and not empty
        if not method:
            available_methods = [choice[0] for choice in self.DetectionMethodChoices.choices()]
            raise ValueError(f"Detection method is required. Available methods: {available_methods}")
        
        # Check if method is valid
        valid_methods = [choice[0] for choice in self.DetectionMethodChoices.choices()]
        if method not in valid_methods:
            raise ValueError(f"Invalid detection method: '{method}'. Available methods: {valid_methods}")
        
        # Execute the appropriate detection method
        if method == self.DetectionMethodChoices.DNN[0]:
            if self.dnn_net is None:
                raise Exception("DNN detection method requested but DNN model is not available. Please ensure model files are present.")
            return self.extract_faces_dnn(image_path, confidence_threshold)
        elif method == self.DetectionMethodChoices.HAAR[0]:
            return self.extract_faces_haar(image_path)