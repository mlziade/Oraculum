from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Picture, Tag, ProcessingQueue
import os

class UploadPictureViewSet(viewsets.ViewSet):
    """
    ViewSet for uploading pictures.
    """
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request):
        """
        Create a barebones picture object and add it to the processing queue.
        """
        # Check if image file is provided
        if 'image' not in request.FILES:
            return Response(
                {"error": "No image file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        image_file = request.FILES['image']
        
        # Get title from request data or use filename as default
        title = request.data.get('title', os.path.splitext(image_file.name)[0])
        
        # Get optional description
        description = request.data.get('description', '')
        
        try:
            # Create barebones Picture object
            picture = Picture.objects.create(
                title=title,
                image=image_file,
                description=description
            )
            
            # Create processing queue entry
            processing_job = ProcessingQueue.objects.create(
                picture=picture,
                status=ProcessingQueue.StatusChoices.PENDING
            )
            
            return Response({
                "message": "Picture uploaded successfully",
                "picture_id": picture.id,
                "processing_job_id": processing_job.id,
                "title": picture.title,
                "status": processing_job.status
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to upload picture: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )