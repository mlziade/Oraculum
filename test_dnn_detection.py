#!/usr/bin/env python3
"""
Test script for OpenCV DNN face detection functionality.
This script demonstrates the new DNN-based face detection method.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraculum.settings')
django.setup()

from recognition.service import FaceExtractionService
import json

def test_dnn_detection():
    """Test the new DNN face detection functionality"""
    
    # Initialize the service
    print("🔧 Initializing FaceExtractionService...")
    service = FaceExtractionService()
    
    # Test images directory
    test_images_dir = Path("testing_images")
    
    if not test_images_dir.exists():
        print("❌ Testing images directory not found!")
        return
    
    # Get a few test images
    test_images = [
        "foto michel - Copia.jpg",
        "istockphoto-1002144354-612x612.jpg",
        "istockphoto-474690025-612x612.jpg"
    ]
    
    print("\n🧪 Testing DNN Face Detection Methods")
    print("=" * 50)
    
    for image_name in test_images:
        image_path = test_images_dir / image_name
        
        if not image_path.exists():
            print(f"⚠️ Image not found: {image_name}")
            continue
            
        print(f"\n📸 Processing: {image_name}")
        print("-" * 30)
        
        try:
            # Test Haar cascade method
            print("🔍 Testing Haar Cascade method...")
            haar_results = service.extract_faces(str(image_path))
            print(f"   Faces detected: {len(haar_results)}")
            if haar_results:
                avg_conf = sum(f['confidence'] for f in haar_results) / len(haar_results)
                print(f"   Average confidence: {avg_conf:.3f}")
            
            # Test DNN method with different confidence thresholds
            print("🧠 Testing DNN Enhanced method...")
            dnn_results = service.extract_faces_dnn(str(image_path), confidence_threshold=0.3)
            print(f"   Faces detected: {len(dnn_results)}")
            if dnn_results:
                avg_conf = sum(f['confidence'] for f in dnn_results) / len(dnn_results)
                print(f"   Average confidence: {avg_conf:.3f}")
            
            # Test method selection
            print("⚙️ Testing method selection...")
            selected_results = service.extract_faces_with_method(str(image_path), method='dnn', confidence_threshold=0.4)
            print(f"   Selected method results: {len(selected_results)} faces")
            
            # Compare methods
            print("📊 Comparing methods...")
            comparison = service.compare_detection_methods(str(image_path), confidence_threshold=0.3)
            print(f"   Haar vs DNN: {comparison['comparison']['difference_in_count']:+d} difference")
            print(f"   DNN high confidence faces: {comparison['comparison']['dnn_higher_confidence']}")
            print(f"   Haar high confidence faces: {comparison['comparison']['haar_higher_confidence']}")
            
        except Exception as e:
            print(f"❌ Error processing {image_name}: {str(e)}")
    
    print("\n✅ DNN Detection testing completed!")

def test_confidence_thresholds():
    """Test different confidence thresholds for DNN detection"""
    
    print("\n🎯 Testing Confidence Thresholds")
    print("=" * 40)
    
    service = FaceExtractionService()
    test_image = Path("testing_images") / "istockphoto-1002144354-612x612.jpg"
    
    if not test_image.exists():
        print("❌ Test image not found!")
        return
    
    thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
    
    for threshold in thresholds:
        try:
            results = service.extract_faces_dnn(str(test_image), confidence_threshold=threshold)
            print(f"Threshold {threshold:.1f}: {len(results)} faces detected")
            
            if results:
                confidences = [f['confidence'] for f in results]
                print(f"   Confidence range: {min(confidences):.3f} - {max(confidences):.3f}")
            
        except Exception as e:
            print(f"❌ Error with threshold {threshold}: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting OpenCV DNN Face Detection Tests")
    print("=" * 50)
    
    test_dnn_detection()
    test_confidence_thresholds()
    
    print("\n🎉 All tests completed!")
