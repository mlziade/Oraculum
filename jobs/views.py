from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import QueueJob

class QueueJobViewSet(viewsets.ViewSet):
    """
    ViewSet for managing queue jobs and checking their status.
    """
    
    def retrieve(self, request, pk=None):
        """
        Get the status of a specific queue job by ID.
        """
        try:
            include_faces = request.query_params.get('faces', 'false').lower() == 'true'
            include_tags = request.query_params.get('tags', 'false').lower() == 'true'
            
            # Build queryset with optimized prefetching
            queryset = QueueJob.objects.select_related('picture')
            
            if include_tags:
                queryset = queryset.prefetch_related('picture__tags')
            
            if include_faces:
                queryset = queryset.prefetch_related('picture__face_extractions')
            
            job = get_object_or_404(
                queryset.only(
                    'id', 'job_type', 'status', 'created_at', 'updated_at',
                    'picture__id', 'picture__title', 'picture__description'
                ),
                pk=pk
            )
            
            # Get associated picture data
            picture_data = {
                'id': job.picture.id,
                'title': job.picture.title,
                'description': job.picture.description,
            }
            
            # Include tags if requested
            if include_tags:
                picture_data['tags'] = [{'id': tag.id, 'name': tag.name} for tag in job.picture.tags.all()]
            
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
                'job_type': job.job_type,
                'status': job.status,
                'created_at': job.created_at,
                'updated_at': job.updated_at,
                'picture': picture_data            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to retrieve job status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request):
        """
        List all queue jobs with optional status and job type filtering.
        """
        status_filter = request.query_params.get('status', None)
        job_type_filter = request.query_params.get('job_type', None)
        include_tags = request.query_params.get('tags', 'false').lower() == 'true'
        include_faces = request.query_params.get('faces', 'false').lower() == 'true'
        
        # Optimize query based on whether tags and faces are needed
        queryset = QueueJob.objects.select_related('picture')
        
        if include_tags:
            queryset = queryset.prefetch_related('picture__tags')
        
        if include_faces:
            queryset = queryset.prefetch_related('picture__face_extractions')
        
        queryset = queryset.only(
            'id', 'job_type', 'status', 'created_at', 'updated_at',
            'picture__id', 'picture__title', 'picture__description'
        )
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if job_type_filter:
            queryset = queryset.filter(job_type=job_type_filter)
        
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
                'job_type': job.job_type,
                'status': job.status,
                'created_at': job.created_at,
                'updated_at': job.updated_at,
                'picture': picture_data            })
        
        return Response({'jobs': jobs}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get queue job statistics including status breakdown and job type counts.
        """
        stats = {
            'total_jobs': QueueJob.objects.count(),
            'pending': QueueJob.objects.filter(status=QueueJob.StatusChoices.PENDING).count(),
            'processing': QueueJob.objects.filter(status=QueueJob.StatusChoices.PROCESSING).count(),
            'completed': QueueJob.objects.filter(status=QueueJob.StatusChoices.COMPLETED).count(),
            'failed': QueueJob.objects.filter(status=QueueJob.StatusChoices.FAILED).count(),
        }
        
        # Add job type breakdown
        for job_type_choice in QueueJob.JobTypeChoices.choices:
            job_type = job_type_choice[0]
            stats[f'{job_type}_jobs'] = QueueJob.objects.filter(job_type=job_type).count()
        
        return Response(stats, status=status.HTTP_200_OK)