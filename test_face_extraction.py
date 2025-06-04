#!/usr/bin/env python
"""
Simple test script for face extraction functionality
Run this to test face extraction on images in the media/pictures directory
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraculum.settings')
django.setup()

from gallery.face_extraction import FaceExtractionService
from gallery.models import Picture
import glob

def test_face_extraction():
    """Test face extraction on available pictures"""
    
    # Initialize the face extraction service
    try:
        face_service = FaceExtractionService()
        print("✓ Face extraction service initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize face extraction service: {e}")
        return
    
    # Get some test images from the media directory
    media_path = os.path.join(os.getcwd(), 'media', 'pictures')
    if not os.path.exists(media_path):
        print(f"✗ Media directory not found: {media_path}")
        return
    
    # Find image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(media_path, ext)))
        image_files.extend(glob.glob(os.path.join(media_path, ext.upper())))
    
    if not image_files:
        print("✗ No image files found in media/pictures directory")
        return
    
    print(f"Found {len(image_files)} image files to test")
    
    # Test face extraction on first few images
    test_count = min(3, len(image_files))
    for i, image_path in enumerate(image_files[:test_count]):
        print(f"\n--- Testing image {i+1}/{test_count}: {os.path.basename(image_path)} ---")
        
        try:
            # Validate image
            if not face_service.validate_image(image_path):
                print(f"✗ Image validation failed for {image_path}")
                continue
            
            # Extract faces
            faces = face_service.extract_faces(image_path)
            
            if faces:
                print(f"✓ Detected {len(faces)} face(s):")
                for j, face in enumerate(faces):
                    print(f"  Face {j+1}: bbox=({face['bbox_x']}, {face['bbox_y']}, {face['bbox_width']}, {face['bbox_height']}), confidence={face['confidence']:.3f}")
            else:
                print("○ No faces detected in this image")
                
        except Exception as e:
            print(f"✗ Error processing {image_path}: {e}")

if __name__ == '__main__':
    print("Testing Face Extraction Service")
    print("=" * 40)
    test_face_extraction()
    print("\nTest completed!")