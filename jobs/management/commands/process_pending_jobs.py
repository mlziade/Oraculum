import json
import os
from django.core.management.base import BaseCommand
from django.core import management


class Command(BaseCommand):
    help = 'DEPRECATED: Use separate commands for face extraction and tagging jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-jobs',
            type=int,
            default=1,
            help='Maximum number of jobs to process in one run'
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific Ollama model to use (must be vision-capable)'
        )
        parser.add_argument(
            '--job-type',
            type=str,
            choices=['face_extraction', 'tagging', 'both'],
            default='both',
            help='Type of jobs to process'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                '⚠️  DEPRECATED: This command is deprecated. Use the new separate commands instead:'
            )
        )
        self.stdout.write('')
        self.stdout.write('For face extraction jobs:')
        self.stdout.write('  python manage.py process_face_extraction_jobs')
        self.stdout.write('')
        self.stdout.write('For tagging jobs:')
        self.stdout.write('  python manage.py process_tagging_jobs')
        self.stdout.write('')
        
        job_type = options.get('job_type', 'both')
        max_jobs = options.get('max_jobs', 1)
        model = options.get('model')
        
        if job_type in ['face_extraction', 'both']:
            self.stdout.write('Running face extraction jobs...')
            management.call_command(
                'process_face_extraction_jobs',
                max_jobs=max_jobs,
                run_once=True
            )
        
        if job_type in ['tagging', 'both']:
            self.stdout.write('Running tagging jobs...')
            cmd_args = ['process_tagging_jobs', f'--max-jobs={max_jobs}', '--run-once']
            if model:
                cmd_args.append(f'--model={model}')
            management.call_command(*cmd_args)
