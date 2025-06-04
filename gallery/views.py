from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from .models import Picture
from jobs.models import QueueJob
from tagging.models import Tag
from recognition.models import FaceExtraction
import os

class UploadPictureViewSet(viewsets.ViewSet):
    """
    ViewSet for uploading pictures.
    """
    parser_classes = [MultiPartParser, FormParser]
    
    def create(self, request):
        """
        Create a barebones picture object and optionally add jobs to the queue.
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
        
        # Get jobs array from URL query parameters
        jobs = request.query_params.getlist('jobs')
        
        # Validate job types if provided
        valid_job_types = [choice[0] for choice in QueueJob.JobTypeChoices.choices]
        invalid_jobs = [job for job in jobs if job not in valid_job_types]
        
        if invalid_jobs:
            return Response(
                {"error": f"Invalid job types: {invalid_jobs}. Valid types are: {valid_job_types}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create barebones Picture object
            picture = Picture.objects.create(
                title=title,
                image=image_file,
                description=description
            )
            
            created_jobs = []
            
            # Create queue jobs if any were specified
            for job_type in jobs:
                queue_job = QueueJob.objects.create(
                    picture=picture,
                    job_type=job_type,
                    status=QueueJob.StatusChoices.PENDING
                )
                created_jobs.append({
                    "job_id": queue_job.id,
                    "job_type": queue_job.job_type,
                    "status": queue_job.status
                })
            
            response_data = {
                "message": "Picture uploaded successfully",
                "picture_id": picture.id,
                "title": picture.title,
                "jobs_created": created_jobs
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to upload picture: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )