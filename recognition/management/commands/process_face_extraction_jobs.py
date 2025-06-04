import os
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from jobs.models import QueueJob
from recognition.models import FaceExtraction
from recognition.service import FaceExtractionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending face extraction jobs from the queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=5,
            help='Maximum number of jobs to process in one run (default: 5)'
        )
        parser.add_argument(
            '--run-once',
            action='store_true',
            help='Run once and exit instead of continuous processing'
        )

    def handle(self, *args, **options):
        max_jobs = options.get('max_jobs', 5)
        run_once = options.get('run_once', False)

        self.stdout.write(
            self.style.SUCCESS(f'Starting face extraction job processor (max_jobs: {max_jobs})...')
        )

        # Initialize Face Extraction service
        try:
            face_extraction_service = FaceExtractionService()
            self.stdout.write('Face extraction service initialized successfully')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Face extraction service initialization failed: {str(e)}')
            )
            return

        if run_once:
            self._process_jobs_once(face_extraction_service, max_jobs)
        else:
            self._process_jobs_continuously(face_extraction_service, max_jobs)

    def _process_jobs_once(self, face_extraction_service, max_jobs):
        """Process jobs once and exit"""
        processed_count, failed_count = self._process_pending_jobs(face_extraction_service, max_jobs)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processing completed. Processed: {processed_count}, Failed: {failed_count}'
            )
        )

    def _process_jobs_continuously(self, face_extraction_service, max_jobs):
        """Process jobs continuously every 15 seconds"""
        import time
        
        self.stdout.write('Starting continuous processing (every 15 seconds)...')
        
        try:
            while True:
                processed_count, failed_count = self._process_pending_jobs(face_extraction_service, max_jobs)
                
                if processed_count > 0 or failed_count > 0:
                    self.stdout.write(
                        f'Batch completed. Processed: {processed_count}, Failed: {failed_count}'
                    )
                
                # Wait 15 seconds before next check
                time.sleep(15)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Face extraction processor stopped by user'))

    def _process_pending_jobs(self, face_extraction_service, max_jobs):
        """Process pending face extraction jobs"""
        processed_count = 0
        failed_count = 0

        # Get pending face extraction jobs
        pending_jobs = QueueJob.objects.filter(
            job_type=QueueJob.JobTypeChoices.FACE_EXTRACTION,
            status=QueueJob.StatusChoices.PENDING
        ).select_related('picture').order_by('created_at')[:max_jobs]

        if not pending_jobs.exists():
            return processed_count, failed_count

        self.stdout.write(f'Found {pending_jobs.count()} pending face extraction job(s) to process.')

        for job in pending_jobs:
            try:
                with transaction.atomic():
                    # Update job status to processing
                    job.status = QueueJob.StatusChoices.PROCESSING
                    job.save()

                    self.stdout.write(
                        f'Processing face extraction job ID {job.id} for picture ID {job.picture.id}: {job.picture.title}'
                    )

                    # Get the image path
                    image_path = job.picture.image.path
                    if not os.path.exists(image_path):
                        raise Exception(f'Image file not found: {image_path}')

                    # Extract faces from the image
                    self._extract_faces(job.picture, image_path, face_extraction_service)

                    # Update job status to completed
                    job.status = QueueJob.StatusChoices.COMPLETED
                    job.save()

                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully processed face extraction job ID {job.id} for picture ID {job.picture.id}'
                        )
                    )

            except Exception as e:
                # Update job status to failed
                job.status = QueueJob.StatusChoices.FAILED
                job.save()

                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to process face extraction job ID {job.id} for picture ID {job.picture.id}: {str(e)}'
                    )
                )
                logger.error(f'Face extraction job {job.id} failed: {str(e)}', exc_info=True)

        return processed_count, failed_count

    def _extract_faces(self, picture, image_path, face_extraction_service):
        """Extract faces from the image and create FaceExtraction objects"""
        try:
            self.stdout.write(f'Starting face extraction for picture ID {picture.id}: {picture.title}')

            # Extract faces using the service
            faces_data = face_extraction_service.extract_faces(image_path)

            if not faces_data:
                self.stdout.write(f'No faces detected in picture ID {picture.id}')
                return

            # Delete existing face extractions for this picture to avoid duplicates
            existing_extractions = FaceExtraction.objects.filter(picture=picture)
            if existing_extractions.exists():
                deleted_count = existing_extractions.count()
                existing_extractions.delete()
                self.stdout.write(f'Removed {deleted_count} existing face extractions for picture ID {picture.id}')

            # Create FaceExtraction objects for each detected face
            created_count = 0
            for face_data in faces_data:
                face_extraction = FaceExtraction.objects.create(
                    picture=picture,
                    bbox_x=face_data['bbox_x'],
                    bbox_y=face_data['bbox_y'],
                    bbox_width=face_data['bbox_width'],
                    bbox_height=face_data['bbox_height'],
                    confidence=face_data['confidence']
                )
                created_count += 1
                self.stdout.write(
                    f'Created face extraction ID {face_extraction.id}: '
                    f'bbox=({face_data["bbox_x"]}, {face_data["bbox_y"]}, {face_data["bbox_width"]}, {face_data["bbox_height"]}), '
                    f'confidence={face_data["confidence"]:.3f}'
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully extracted {created_count} faces from picture ID {picture.id}: {picture.title}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to extract faces from picture ID {picture.id}: {str(e)}')
            )
            raise  # Re-raise to mark job as failed
