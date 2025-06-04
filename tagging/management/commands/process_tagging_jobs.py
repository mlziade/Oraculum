import json
import os
import logging
import platform
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
                    self.stdout.write(
                        self.style.WARNING('Another tagging job processor is already running. Exiting.')
                    )
                    return

                self.stdout.write(
                    self.style.SUCCESS(f'Starting tagging job processor (max_jobs: {max_jobs})...')
                )

                # Initialize Ollama service
                ollama_service = OllamaService()

                # Check if Ollama server is running
                if not ollama_service.is_server_running():
                    self.stdout.write(
                        self.style.ERROR('Ollama server is not running. Please start Ollama first.')
                    )
                    return

                # Load the tags prompt and replace template variables
                prompt_template = self._load_prompt_template()
                if not prompt_template:
                    return

                if run_once:
                    self._process_jobs_once(ollama_service, prompt_template, model, max_jobs)
                else:
                    self._process_jobs_continuously(ollama_service, prompt_template, model, max_jobs)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in tagging job processor: {str(e)}')
            )
            logger.error(f'Tagging job processor error: {str(e)}', exc_info=True)
        finally:
            # Clean up lock file
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)

    def _process_jobs_once(self, ollama_service, prompt_template, model, max_jobs):
        """Process jobs once and exit"""
        processed_count, failed_count = self._process_pending_jobs(ollama_service, prompt_template, model, max_jobs)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processing completed. Processed: {processed_count}, Failed: {failed_count}'
            )
        )

    def _process_jobs_continuously(self, ollama_service, prompt_template, model, max_jobs):
        """Process jobs continuously every 2 minutes"""
        import time
        
        self.stdout.write('Starting continuous processing (every 2 minutes)...')
        
        try:
            while True:
                processed_count, failed_count = self._process_pending_jobs(ollama_service, prompt_template, model, max_jobs)
                
                if processed_count > 0 or failed_count > 0:
                    self.stdout.write(
                        f'Batch completed. Processed: {processed_count}, Failed: {failed_count}'
                    )
                
                # Wait 2 minutes before next check
                time.sleep(120)
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Tagging processor stopped by user'))

    def _load_prompt_template(self):
        """Load and prepare the prompt template"""
        prompt_path = os.path.join(settings.BASE_DIR, 'tagging', 'prompts', 'tags_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Tags prompt file not found at: {prompt_path}')
            )
            return None

        # Replace template variables
        return self._replace_template_variables(prompt_template)

    def _replace_template_variables(self, prompt_template):
        """Replace template variables in the prompt with actual data"""
        # Get all tag classifications from the database
        classifications = TagClassification.objects.all()
        
        if classifications.exists():
            classifications_text = ", ".join([f'"{cls.name}"' for cls in classifications])
        else:
            # Default classifications if none exist in database
            classifications_text = '"Living Things", "Inanimate Objects", "Locations", "Actions", "Environmental", "Descriptive", "Temporal"'
        
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
            self.stdout.write(
                self.style.WARNING(f'Tagging job already processing (ID: {processing_jobs.first().id}). Skipping this run.')
            )
            return processed_count, failed_count

        # Get pending tagging jobs
        pending_jobs = QueueJob.objects.filter(
            job_type=QueueJob.JobTypeChoices.TAGS,
            status=QueueJob.StatusChoices.PENDING
        ).select_related('picture').order_by('created_at')[:max_jobs]

        if not pending_jobs.exists():
            return processed_count, failed_count

        self.stdout.write(f'Found {pending_jobs.count()} pending tagging job(s) to process.')

        for job in pending_jobs:
            try:
                with transaction.atomic():
                    # Update job status to processing
                    job.status = QueueJob.StatusChoices.PROCESSING
                    job.save()

                    self.stdout.write(
                        f'Processing tagging job ID {job.id} for picture ID {job.picture.id}: {job.picture.title}'
                    )

                    # Get the image path
                    image_path = job.picture.image.path
                    if not os.path.exists(image_path):
                        raise Exception(f'Image file not found: {image_path}')

                    # Use specified model or default vision model
                    vision_model = model
                    if not vision_model:
                        available_models = ollama_service.get_vision_models()
                        if available_models:
                            vision_model = available_models[0]  # Use first available vision model
                        else:
                            raise Exception('No vision models available')

                    # Generate tags using Ollama
                    self.stdout.write(f'Generating tags using model: {vision_model}')
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
                        else:
                            raise ValueError('No valid JSON found in response')
                    except (json.JSONDecodeError, ValueError) as e:
                        self.stdout.write(
                            self.style.WARNING(f'Failed to parse JSON response for job ID {job.id}: {e}')
                        )
                        # Try to extract tags from plain text response
                        tags_data = self._extract_tags_from_text(response)

                    # Process and save tags
                    self._process_tags(job.picture, tags_data)

                    # Update job status to completed
                    job.status = QueueJob.StatusChoices.COMPLETED
                    job.save()

                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Successfully processed tagging job ID {job.id} for picture ID {job.picture.id}'
                        )
                    )

            except Exception as e:
                # Update job status to failed
                job.status = QueueJob.StatusChoices.FAILED
                job.save()

                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to process tagging job ID {job.id} for picture ID {job.picture.id}: {str(e)}'
                    )
                )
                logger.error(f'Tagging job {job.id} failed: {str(e)}', exc_info=True)

        return processed_count, failed_count

    def _process_tags(self, picture, tags_data):
        """Process and save tags to the picture with classifications"""
        if not isinstance(tags_data, dict):
            return

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
                        classification, _ = TagClassification.objects.get_or_create(
                            name=classification_name
                        )
                        
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
                        classification, _ = TagClassification.objects.get_or_create(
                            name=classification_name
                        )
                        
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
                            all_tags.append((tag_name, None))

        # Create or get tags and associate with picture
        created_tags_count = 0
        for tag_name, classification in all_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_name.lower().strip(),
                defaults={
                    'description': f'Auto-generated tag from image analysis',
                    'classification': classification
                }
            )
            
            # Update classification if tag exists but doesn't have one
            if not created and not tag.classification and classification:
                tag.classification = classification
                tag.save()
            
            picture.tags.add(tag)
            if created:
                created_tags_count += 1
                self.stdout.write(f'Created new tag ID {tag.id}: {tag.name} (Classification: {classification.name if classification else "None"})')

        self.stdout.write(
            f'Added {len(all_tags)} tags to picture ID {picture.id}: {picture.title} '
            f'({created_tags_count} new tags created)'
        )

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
