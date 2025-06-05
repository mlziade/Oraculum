from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from .models import Picture
from jobs.models import QueueJob
from tagging.models import Tag
from recognition.models import FaceExtraction
from .service import query_picture_by_tags, serialize_pictures, serialize_pictures_list
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

class QueryingPicturesViewSet(viewsets.ViewSet):
    """
    ViewSet for querying pictures based on various criteria.
    """
    
    @action(detail=False, methods=['get'])
    def by_tags(self, request):
        """
        API endpoint to query pictures by tags using OR logic (non-additive).
        Returns pictures that have ANY of the specified tags.
        
        Query parameters:
        - tags: Comma-separated list of tag names (e.g., ?tags=ok,bla)
        - detailed: Boolean to control output detail level (default: true)
                   true = full details with all tag information
                   false = simplified output with tag count only
        """
        # Get tags from query parameters
        tags_param = request.query_params.get('tags', '')
        
        if not tags_param:
            return Response(
                {"error": "No tags provided. Use ?tags=tag1,tag2,tag3 format"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Split tags by comma and clean them
        tag_names = [tag.strip().lower() for tag in tags_param.split(',') if tag.strip()]
        
        if not tag_names:
            return Response(
                {"error": "No valid tags provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use the service function to get pictures
            pictures = query_picture_by_tags(tag_names)
            
            # Check if detailed output is requested
            detailed = request.query_params.get('detailed', 'true').lower() == 'true'
            
            # Serialize the results using the appropriate serializer
            if detailed:
                pictures_data = serialize_pictures(pictures)
            else:
                pictures_data = serialize_pictures_list(pictures)
            
            return Response({
                "message": f"Found {len(pictures_data)} pictures with tags: {', '.join(tag_names)}",
                "query_tags": tag_names,
                "total_results": len(pictures_data),
                "pictures": pictures_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to query pictures: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )