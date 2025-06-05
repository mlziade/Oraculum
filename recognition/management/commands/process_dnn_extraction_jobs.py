import os
import logging
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from jobs.models import QueueJob
from recognition.models import FaceExtraction
from recognition.service import FaceExtractionService

# Configure logging for this command
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [DNN_EXTRACTION] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process pending DNN face extraction jobs from the queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=3,
            help='Maximum number of jobs to process in one run (default: 3, lower due to DNN complexity)'
        )
        parser.add_argument(
            '--run-once',
            action='store_true',
            help='Run once and exit instead of continuous processing'
        )
        parser.add_argument(
            '--confidence-threshold',
            type=float,
            default=0.5,
            help='Minimum confidence threshold for DNN face detection (default: 0.5)'
        )

    def handle(self, *args, **options):
        max_jobs = options.get('max_jobs', 3)
        run_once = options.get('run_once', False)
        confidence_threshold = options.get('confidence_threshold', 0.5)

        start_message = f'🧠 Starting DNN face extraction job processor (max_jobs: {max_jobs}, confidence: {confidence_threshold})'
        self.stdout.write(self.style.SUCCESS(start_message))
        logger.info(start_message)

        # Initialize Face Extraction service
        try:
            face_extraction_service = FaceExtractionService()
            init_message = '✅ DNN face extraction service initialized successfully'
            self.stdout.write(init_message)
            logger.info(init_message)
        except Exception as e:
            error_message = f'❌ DNN face extraction service initialization failed: {str(e)}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message, exc_info=True)
            return

        if run_once:
            self._process_jobs_once(face_extraction_service, max_jobs, confidence_threshold)
        else:
            self._process_jobs_continuously(face_extraction_service, max_jobs, confidence_threshold)

    def _process_jobs_once(self, face_extraction_service, max_jobs, confidence_threshold):
        """Process jobs once and exit"""
        logger.info(f'🎯 Processing DNN face extraction jobs once (max: {max_jobs}, confidence: {confidence_threshold})')
        processed_count, failed_count = self._process_pending_jobs(face_extraction_service, max_jobs, confidence_threshold)
        
        completion_message = f'✅ DNN face extraction processing completed. Processed: {processed_count}, Failed: {failed_count}'
        self.stdout.write(self.style.SUCCESS(completion_message))
        logger.info(completion_message)

    def _process_jobs_continuously(self, face_extraction_service, max_jobs, confidence_threshold):
        """Process jobs continuously every 30 seconds (longer due to DNN complexity)"""
        
        start_message = '🔄 Starting continuous DNN face extraction processing (every 30 seconds)...'
        self.stdout.write(start_message)
        logger.info(start_message)
        
        try:
            while True:
                logger.info('🧠 Checking for pending DNN face extraction jobs...')
                processed_count, failed_count = self._process_pending_jobs(face_extraction_service, max_jobs, confidence_threshold)
                
                if processed_count > 0 or failed_count > 0:
                    batch_message = f'📊 DNN face extraction batch completed. Processed: {processed_count}, Failed: {failed_count}'
                    self.stdout.write(batch_message)
                    logger.info(batch_message)
                else:
                    logger.debug('No DNN face extraction jobs to process')
                
                logger.info('⏳ Waiting 30 seconds before next DNN face extraction check...')
                # Wait 30 seconds before next check (longer due to complexity)
                time.sleep(30)
                
        except KeyboardInterrupt:
            stop_message = '⚠️ DNN face extraction processor stopped by user'
            self.stdout.write(self.style.WARNING(stop_message))
            logger.warning(stop_message)

    def _process_pending_jobs(self, face_extraction_service, max_jobs, confidence_threshold):
        """Process pending DNN face extraction jobs"""
        processed_count = 0
        failed_count = 0

        # Get pending DNN face extraction jobs
        pending_jobs = QueueJob.objects.filter(
            job_type=QueueJob.JobTypeChoices.FACE_EXTRACTION_DNN,
            status=QueueJob.StatusChoices.PENDING
        ).select_related('picture').order_by('created_at')[:max_jobs]

        if not pending_jobs.exists():
            logger.debug('No pending DNN face extraction jobs found')
            return processed_count, failed_count

        job_count_message = f'📋 Found {pending_jobs.count()} pending DNN face extraction job(s) to process'
        self.stdout.write(job_count_message)
        logger.info(job_count_message)

        for job in pending_jobs:
            job_start_time = time.time()
            try:
                with transaction.atomic():
                    # Update job status to processing
                    job.status = QueueJob.StatusChoices.PROCESSING
                    job.save()

                    processing_message = f'⚙️ Processing DNN face extraction job ID {job.id} for picture ID {job.picture.id}: {job.picture.title}'
                    self.stdout.write(processing_message)
                    logger.info(processing_message)

                    # Get the image path
                    image_path = job.picture.image.path
                    if not os.path.exists(image_path):
                        raise Exception(f'Image file not found: {image_path}')

                    # Extract faces from the image using DNN
                    self._extract_faces_dnn(job.picture, image_path, face_extraction_service, confidence_threshold)

                    # Update job status to completed
                    job.status = QueueJob.StatusChoices.COMPLETED
                    job.save()

                    job_duration = time.time() - job_start_time
                    processed_count += 1
                    success_message = f'✅ Successfully processed DNN face extraction job ID {job.id} for picture ID {job.picture.id} in {job_duration:.2f}s'
                    self.stdout.write(self.style.SUCCESS(success_message))
                    logger.info(success_message)

            except Exception as e:
                # Update job status to failed
                job.status = QueueJob.StatusChoices.FAILED
                job.save()

                job_duration = time.time() - job_start_time
                failed_count += 1
                error_message = f'❌ Failed to process DNN face extraction job ID {job.id} for picture ID {job.picture.id} after {job_duration:.2f}s: {str(e)}'
                self.stdout.write(self.style.ERROR(error_message))
                logger.error(error_message, exc_info=True)

        return processed_count, failed_count

    def _extract_faces_dnn(self, picture, image_path, face_extraction_service, confidence_threshold):
        """Extract faces from the image using DNN and create FaceExtraction objects"""
        try:
            extraction_start_message = f'🧠 Starting DNN face extraction for picture ID {picture.id}: {picture.title} (confidence: {confidence_threshold})'
            self.stdout.write(extraction_start_message)
            logger.info(extraction_start_message)

            # Extract faces using the DNN service
            faces_data = face_extraction_service.extract_faces_dnn(image_path, confidence_threshold)

            if not faces_data:
                no_faces_message = f'👤 No faces detected in picture ID {picture.id} using DNN (confidence >= {confidence_threshold})'
                self.stdout.write(no_faces_message)
                logger.info(no_faces_message)
                return

            # Delete existing DNN face extractions for this picture to avoid duplicates
            existing_extractions = FaceExtraction.objects.filter(
                picture=picture,
                algorithm=FaceExtraction.AlgorithmChoices.DNN
            )
            if existing_extractions.exists():
                deleted_count = existing_extractions.count()
                existing_extractions.delete()
                cleanup_message = f'🧹 Removed {deleted_count} existing DNN face extractions for picture ID {picture.id}'
                self.stdout.write(cleanup_message)
                logger.info(cleanup_message)

            # Create FaceExtraction objects for each detected face
            created_count = 0
            for face_data in faces_data:
                face_extraction = FaceExtraction.objects.create(
                    picture=picture,
                    bbox_x=face_data['bbox_x'],
                    bbox_y=face_data['bbox_y'],
                    bbox_width=face_data['bbox_width'],
                    bbox_height=face_data['bbox_height'],
                    confidence=face_data['confidence'],
                    algorithm=FaceExtraction.AlgorithmChoices.DNN
                )
                created_count += 1
                detection_type = face_data.get('detection_type', 'dnn_enhanced')
                face_created_message = (f'🤖 Created DNN face extraction ID {face_extraction.id} ({detection_type}): '
                    f'bbox=({face_data["bbox_x"]}, {face_data["bbox_y"]}, {face_data["bbox_width"]}, {face_data["bbox_height"]}), '
                    f'confidence={face_data["confidence"]:.3f}')
                self.stdout.write(face_created_message)
                logger.info(face_created_message)

            success_extraction_message = f'✅ Successfully extracted {created_count} faces from picture ID {picture.id} using DNN: {picture.title}'
            self.stdout.write(self.style.SUCCESS(success_extraction_message))
            logger.info(success_extraction_message)

        except Exception as e:
            error_extraction_message = f'❌ Failed to extract faces from picture ID {picture.id} using DNN: {str(e)}'
            self.stdout.write(self.style.ERROR(error_extraction_message))
            logger.error(error_extraction_message, exc_info=True)
            raise  # Re-raise to mark job as failed
