from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from .models import Picture, Tag, ProcessingQueue, FaceExtraction
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

class ProcessingQueueViewSet(viewsets.ViewSet):
    """
    ViewSet for checking processing queue status.
    """
    def retrieve(self, request, pk=None):
        """
        Get the status of a specific processing job by ID.
        """
        try:
            include_faces = request.query_params.get('faces', 'false').lower() == 'true'
            
            # Build queryset with optimized prefetching
            queryset = ProcessingQueue.objects.select_related('picture').prefetch_related('picture__tags')
            
            if include_faces:
                queryset = queryset.prefetch_related('picture__face_extractions')
            
            job = get_object_or_404(
                queryset.only(
                    'id', 'status', 'created_at', 'updated_at',
                    'picture__id', 'picture__title', 'picture__description'
                ),
                pk=pk
            )
            
            # Get associated picture and tags
            picture_data = {
                'id': job.picture.id,
                'title': job.picture.title,
                'description': job.picture.description,
                'tags': [{'id': tag.id, 'name': tag.name} for tag in job.picture.tags.all()]
            }
            
            # Include face extractions if requested
            if include_faces:
                picture_data['face_extractions'] = [
                    {
                        'id': face.id,
                        'bbox_x': face.bbox_x,
                        'bbox_y': face.bbox_y,
                        'bbox_width': face.bbox_width,
                        'bbox_height': face.bbox_height,
                        'confidence': face.confidence,
                        'created_at': face.created_at
                    }
                    for face in job.picture.face_extractions.all()
                ]
            
            response_data = {
                'job_id': job.id,
                'status': job.status,
                'created_at': job.created_at,
                'updated_at': job.updated_at,
                'picture': picture_data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve job status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request):
        """
        List all processing jobs with optional status filtering.
        """
        status_filter = request.query_params.get('status', None)
        include_tags = request.query_params.get('tags', 'false').lower() == 'true'
        include_faces = request.query_params.get('faces', 'false').lower() == 'true'
        
        # Optimize query based on whether tags and faces are needed
        queryset = ProcessingQueue.objects.select_related('picture')
        
        if include_tags:
            queryset = queryset.prefetch_related('picture__tags')
        
        if include_faces:
            queryset = queryset.prefetch_related('picture__face_extractions')
        
        queryset = queryset.only(
            'id', 'status', 'created_at', 'updated_at',
            'picture__id', 'picture__title', 'picture__description'
        )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        jobs = []
        for job in queryset.order_by('-created_at'):
            picture_data = {
                'id': job.picture.id,
                'title': job.picture.title,
                'description': job.picture.description,
            }
            
            # Only include tags if requested
            if include_tags:
                picture_data['tags'] = [{'id': tag.id, 'name': tag.name} for tag in job.picture.tags.all()]
            
            # Only include face extractions if requested
            if include_faces:
                picture_data['face_extractions'] = [
                    {
                        'id': face.id,
                        'bbox_x': face.bbox_x,
                        'bbox_y': face.bbox_y,
                        'bbox_width': face.bbox_width,
                        'bbox_height': face.bbox_height,
                        'confidence': face.confidence,
                        'created_at': face.created_at
                    }
                    for face in job.picture.face_extractions.all()
                ]
            
            jobs.append({
                'job_id': job.id,
                'status': job.status,
                'created_at': job.created_at,
                'updated_at': job.updated_at,
                'picture': picture_data
            })
        
        return Response({'jobs': jobs}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get processing queue statistics.
        """
        stats = {
            'total_jobs': ProcessingQueue.objects.count(),
            'pending': ProcessingQueue.objects.filter(status=ProcessingQueue.StatusChoices.PENDING).count(),
            'processing': ProcessingQueue.objects.filter(status=ProcessingQueue.StatusChoices.PROCESSING).count(),
            'completed': ProcessingQueue.objects.filter(status=ProcessingQueue.StatusChoices.COMPLETED).count(),
            'failed': ProcessingQueue.objects.filter(status=ProcessingQueue.StatusChoices.FAILED).count(),
        }
        
        return Response(stats, status=status.HTTP_200_OK)