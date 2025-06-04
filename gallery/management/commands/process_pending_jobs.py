import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from gallery.models import ProcessingQueue, Picture, Tag, TagClassification
from gallery.ollama import OllamaService


class Command(BaseCommand):
    help = 'Process pending jobs in the processing queue using Ollama vision models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=10,
            help='Maximum number of jobs to process in one run (default: 10)'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific Ollama model to use (must be vision-capable)'
        )

    def handle(self, *args, **options):
        max_jobs = options['max_jobs']
        model = options.get('model')
        
        self.stdout.write(self.style.SUCCESS(f'Starting to process up to {max_jobs} pending jobs...'))
        
        # Initialize Ollama service
        ollama_service = OllamaService()
        
        # Check if Ollama server is running
        if not ollama_service.is_server_running():
            self.stdout.write(
                self.style.ERROR('Ollama server is not running. Please start Ollama first.')
            )
            return
        
        # Load the tags prompt and replace template variables
        prompt_path = os.path.join(settings.BASE_DIR, 'gallery', 'prompts', 'tags_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Tags prompt file not found at: {prompt_path}')
            )
            return
        
        # Replace template variables
        prompt_template = self._replace_template_variables(prompt_template)
        
        # Get pending jobs
        pending_jobs = ProcessingQueue.objects.filter(
            status=ProcessingQueue.StatusChoices.PENDING
        ).select_related('picture').order_by('created_at')[:max_jobs]
        
        if not pending_jobs:
            self.stdout.write(self.style.WARNING('No pending jobs found.'))
            return
        
        self.stdout.write(f'Found {len(pending_jobs)} pending jobs to process.')
        
        processed_count = 0
        failed_count = 0
        
        for job in pending_jobs:
            try:
                self.stdout.write(f'Processing job ID {job.id} for picture ID {job.picture.id}: {job.picture.title}')
                
                # Update job status to processing
                job.status = ProcessingQueue.StatusChoices.PROCESSING
                job.save()
                
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
                job.status = ProcessingQueue.StatusChoices.COMPLETED
                job.save()
                
                processed_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully processed job ID {job.id} for picture ID {job.picture.id}')
                )
                
            except Exception as e:
                # Update job status to failed
                job.status = ProcessingQueue.StatusChoices.FAILED
                job.save()
                
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Failed to process job ID {job.id} for picture ID {job.picture.id}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'Processing completed. Processed: {processed_count}, Failed: {failed_count}'
            )
        )
    
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
        # You might want to implement more sophisticated parsing
        tags_data = {"general": []}
        
        # Simple pattern matching for common words
        words = text.lower().replace(',', ' ').replace('.', ' ').split()
        # Filter out common words and keep potential tags
        potential_tags = [word for word in words if len(word) > 2 and word.isalpha()]
        tags_data["general"] = potential_tags[:20]  # Limit to 20 tags
        
        return tags_data
