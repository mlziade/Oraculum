import json
import os
import logging
import platform
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from jobs.models import QueueJob
from tagging.models import Tag, TagClassification
from tagging.ollama import OllamaService

# Platform-specific imports for file locking
if platform.system() == 'Windows':
    import msvcrt
else:
    import fcntl

# Configure logging for this command
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [TAGGING] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending tagging jobs from the queue using Ollama vision models (single instance only)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=3,
            help='Maximum number of jobs to process in one run (default: 3)'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific Ollama model to use (must be vision-capable)'
        )
        parser.add_argument(
            '--run-once',
            action='store_true',
            help='Run once and exit instead of continuous processing'
        )

    def handle(self, *args, **options):
        max_jobs = options.get('max_jobs', 3)
        model = options.get('model')
        run_once = options.get('run_once', False)        # Ensure only one instance runs at a time
        lock_file_path = os.path.join(settings.BASE_DIR, 'tagging_job.lock')
        
        try:
            with open(lock_file_path, 'w') as lock_file:
                try:
                    # Platform-specific file locking
                    if platform.system() == 'Windows':
                        # Try to lock the file on Windows
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        # Try to acquire exclusive lock (non-blocking) on Unix
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    lock_message = '⚠️ Another tagging job processor is already running. Exiting.'
                    self.stdout.write(self.style.WARNING(lock_message))
                    logger.warning(lock_message)
                    return

                start_message = f'🏷️ Starting tagging job processor (max_jobs: {max_jobs})'
                if model:
                    start_message += f' using model: {model}'
                self.stdout.write(self.style.SUCCESS(start_message))
                logger.info(start_message)

                # Initialize Ollama service
                ollama_service = OllamaService()

                # Check if Ollama server is running
                if not ollama_service.is_server_running():
                    error_message = '❌ Ollama server is not running. Please start Ollama first.'
                    self.stdout.write(self.style.ERROR(error_message))
                    logger.error(error_message)
                    return
                else:
                    server_message = '✅ Ollama server is running'
                    logger.info(server_message)

                # Load the tags prompt and replace template variables
                prompt_template = self._load_prompt_template()
                if not prompt_template:
                    return

                if run_once:
                    self._process_jobs_once(ollama_service, prompt_template, model, max_jobs)
                else:
                    self._process_jobs_continuously(ollama_service, prompt_template, model, max_jobs)

        except Exception as e:
            error_message = f'❌ Error in tagging job processor: {str(e)}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message, exc_info=True)
        finally:
            # Clean up lock file
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
                logger.info('🧹 Cleaned up lock file')

    def _process_jobs_once(self, ollama_service, prompt_template, model, max_jobs):
        """Process jobs once and exit"""
        logger.info(f'🎯 Processing tagging jobs once (max: {max_jobs})')
        processed_count, failed_count = self._process_pending_jobs(ollama_service, prompt_template, model, max_jobs)
        
        completion_message = f'✅ Tagging processing completed. Processed: {processed_count}, Failed: {failed_count}'
        self.stdout.write(self.style.SUCCESS(completion_message))
        logger.info(completion_message)

    def _process_jobs_continuously(self, ollama_service, prompt_template, model, max_jobs):
        """Process jobs continuously every 2 minutes"""
        
        start_message = '🔄 Starting continuous tagging processing (every 2 minutes)...'
        self.stdout.write(start_message)
        logger.info(start_message)
        
        try:
            while True:
                logger.info('🏷️ Checking for pending tagging jobs...')
                processed_count, failed_count = self._process_pending_jobs(ollama_service, prompt_template, model, max_jobs)
                
                if processed_count > 0 or failed_count > 0:
                    batch_message = f'📊 Tagging batch completed. Processed: {processed_count}, Failed: {failed_count}'
                    self.stdout.write(batch_message)
                    logger.info(batch_message)
                else:
                    logger.debug('No tagging jobs to process')
                
                logger.info('⏳ Waiting 2 minutes before next tagging check...')
                # Wait 2 minutes before next check
                time.sleep(120)
                
        except KeyboardInterrupt:
            stop_message = '⚠️ Tagging processor stopped by user'
            self.stdout.write(self.style.WARNING(stop_message))
            logger.warning(stop_message)

    def _load_prompt_template(self):
        """Load and prepare the prompt template"""
        prompt_path = os.path.join(settings.BASE_DIR, 'tagging', 'prompts', 'tags_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            logger.info(f'📄 Loaded prompt template from: {prompt_path}')
        except FileNotFoundError:
            error_message = f'❌ Tags prompt file not found at: {prompt_path}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message)
            return None

        # Replace template variables
        return self._replace_template_variables(prompt_template)

    def _replace_template_variables(self, prompt_template):
        """Replace template variables in the prompt with actual data"""
        # Get all tag classifications from the database
        classifications = TagClassification.objects.all()
        
        if classifications.exists():
            classifications_text = ", ".join([f'"{cls.name}"' for cls in classifications])
            logger.info(f'📂 Using {classifications.count()} tag classifications from database')
        else:
            # Default classifications if none exist in database
            classifications_text = '"Living Things", "Inanimate Objects", "Locations", "Actions", "Environmental", "Descriptive", "Temporal"'
            logger.info('📂 Using default tag classifications')
        
        # Replace the template variable
        prompt_template = prompt_template.replace('{{classifications}}', classifications_text)
        
        return prompt_template

    def _process_pending_jobs(self, ollama_service, prompt_template, model, max_jobs):
        """Process pending tagging jobs"""
        processed_count = 0
        failed_count = 0

        # Check if any tagging job is currently processing
        processing_jobs = QueueJob.objects.filter(
            job_type=QueueJob.JobTypeChoices.TAGS,
            status=QueueJob.StatusChoices.PROCESSING
        )
        
        if processing_jobs.exists():
            skip_message = f'⚠️ Tagging job already processing (ID: {processing_jobs.first().id}). Skipping this run.'
            self.stdout.write(self.style.WARNING(skip_message))
            logger.warning(skip_message)
            return processed_count, failed_count

        # Get pending tagging jobs
        pending_jobs = QueueJob.objects.filter(
            job_type=QueueJob.JobTypeChoices.TAGS,
            status=QueueJob.StatusChoices.PENDING
        ).select_related('picture').order_by('created_at')[:max_jobs]

        if not pending_jobs.exists():
            logger.debug('No pending tagging jobs found')
            return processed_count, failed_count

        job_count_message = f'📋 Found {pending_jobs.count()} pending tagging job(s) to process'
        self.stdout.write(job_count_message)
        logger.info(job_count_message)

        for job in pending_jobs:
            job_start_time = time.time()
            try:
                with transaction.atomic():
                    # Update job status to processing
                    job.status = QueueJob.StatusChoices.PROCESSING
                    job.save()

                    processing_message = f'⚙️ Processing tagging job ID {job.id} for picture ID {job.picture.id}: {job.picture.title}'
                    self.stdout.write(processing_message)
                    logger.info(processing_message)

                    # Get the image path
                    image_path = job.picture.image.path
                    if not os.path.exists(image_path):
                        raise Exception(f'Image file not found: {image_path}')

                    # Use specified model or default vision model
                    vision_model = model
                    if not vision_model:
                        available_models = ollama_service.get_vision_models()
                        if available_models:
                            # Try to use default model from settings first
                            default_model = getattr(settings, 'OLLAMA_DEFAULT_MODEL', None)
                            if default_model and default_model in available_models:
                                vision_model = default_model
                                logger.info(f'🤖 Using default vision model from settings: {vision_model}')
                            else:
                                vision_model = available_models[0]  # Use first available vision model
                                logger.info(f'🤖 Using first available vision model: {vision_model}')
                        else:
                            raise Exception('No vision models available')
                    else:
                        logger.info(f'🤖 Using specified model: {vision_model}')

                    # Generate tags using Ollama
                    generation_message = f'🧠 Generating tags using model: {vision_model}'
                    self.stdout.write(generation_message)
                    logger.info(generation_message)
                    
                    response = ollama_service.generate_with_image(
                        prompt=prompt_template,
                        image_paths=image_path,
                        model=vision_model
                    )

                    # Parse the JSON response
                    try:
                        # Extract JSON from response (in case there's additional text)
                        json_start = response.find('{')
                        json_end = response.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            json_response = response[json_start:json_end]
                            tags_data = json.loads(json_response)
                            logger.info('✅ Successfully parsed JSON response from AI')
                        else:
                            raise ValueError('No valid JSON found in response')
                    except (json.JSONDecodeError, ValueError) as e:
                        parse_warning_message = f'⚠️ Failed to parse JSON response for job ID {job.id}: {e}'
                        self.stdout.write(self.style.WARNING(parse_warning_message))
                        logger.warning(parse_warning_message)
                        # Try to extract tags from plain text response
                        tags_data = self._extract_tags_from_text(response)
                        logger.info('🔄 Using fallback text extraction for tags')

                    # Process and save tags
                    self._process_tags(job.picture, tags_data)

                    # Update job status to completed
                    job.status = QueueJob.StatusChoices.COMPLETED
                    job.save()

                    job_duration = time.time() - job_start_time
                    processed_count += 1
                    success_message = f'✅ Successfully processed tagging job ID {job.id} for picture ID {job.picture.id} in {job_duration:.2f}s'
                    self.stdout.write(self.style.SUCCESS(success_message))
                    logger.info(success_message)

            except Exception as e:
                # Update job status to failed
                job.status = QueueJob.StatusChoices.FAILED
                job.save()

                job_duration = time.time() - job_start_time
                failed_count += 1
                error_message = f'❌ Failed to process tagging job ID {job.id} for picture ID {job.picture.id} after {job_duration:.2f}s: {str(e)}'
                self.stdout.write(self.style.ERROR(error_message))
                logger.error(error_message, exc_info=True)

        return processed_count, failed_count

    def _process_tags(self, picture, tags_data):
        """Process and save tags to the picture with classifications"""
        if not isinstance(tags_data, dict):
            logger.warning(f'Invalid tags data format for picture ID {picture.id}')
            return

        logger.info(f'🏷️ Processing tags for picture ID {picture.id}: {picture.title}')

        # Handle the new structure with tags_with_classifications array
        if 'tags_with_classifications' in tags_data:
            tags_array = tags_data['tags_with_classifications']
            
            # Process new array format: [{"tag": "dog", "classification": "Living Things"}, ...]
            if isinstance(tags_array, list):
                all_tags = []
                for tag_obj in tags_array:
                    if isinstance(tag_obj, dict) and 'tag' in tag_obj and 'classification' in tag_obj:
                        tag_name = tag_obj['tag']
                        classification_name = tag_obj['classification']
                        
                        # Get or create the classification
                        classification, created = TagClassification.objects.get_or_create(
                            name=classification_name
                        )
                        if created:
                            logger.info(f'📂 Created new tag classification: {classification_name}')
                        
                        if tag_name and isinstance(tag_name, str):
                            all_tags.append((tag_name, classification))
            else:
                # Handle legacy nested format
                all_tags = []
                for category, category_data in tags_array.items():
                    if isinstance(category_data, dict):
                        tags_list = category_data.get('tags', [])
                        classification_name = category_data.get('classification', 'General')
                        
                        # Get or create the classification
                        classification, created = TagClassification.objects.get_or_create(
                            name=classification_name
                        )
                        if created:
                            logger.info(f'📂 Created new tag classification: {classification_name}')
                        
                        for tag_name in tags_list:
                            if tag_name and isinstance(tag_name, str):
                                all_tags.append((tag_name, classification))
        else:
            # Handle legacy format without classifications
            all_tags = []
            for category, tags_list in tags_data.items():
                if isinstance(tags_list, list):
                    for tag_name in tags_list:
                        if tag_name and isinstance(tag_name, str):
                            all_tags.append((tag_name, None))        # Create or get tags and associate with picture
        created_tags_count = 0
        for tag_name, classification in all_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_name.lower().strip(),
                defaults={
                    'classification': classification
                }
            )
            
            # Update classification if tag exists but doesn't have one
            if not created and not tag.classification and classification:
                tag.classification = classification
                tag.save()
                logger.info(f'🏷️ Updated classification for existing tag: {tag.name}')
            
            picture.tags.add(tag)
            if created:
                created_tags_count += 1
                tag_created_message = f'🏷️ Created new tag ID {tag.id}: {tag.name} (Classification: {classification.name if classification else "None"})'
                self.stdout.write(tag_created_message)
                logger.info(tag_created_message)

        tags_summary_message = f'✅ Added {len(all_tags)} tags to picture ID {picture.id}: {picture.title} ({created_tags_count} new tags created)'
        self.stdout.write(tags_summary_message)
        logger.info(tags_summary_message)

    def _extract_tags_from_text(self, text):
        """Fallback method to extract tags from plain text response"""
        # This is a simple fallback - look for comma-separated words
        tags_data = {"general": []}
        
        # Simple pattern matching for common words
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        # Filter out common words and keep potential tags
        potential_tags = [word for word in words if len(word) > 2 and word.isalpha()]
        tags_data["general"] = potential_tags[:20]  # Limit to 20 tags
        
        return tags_data
