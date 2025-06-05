import logging
from django.core.management.base import BaseCommand

# Configure logging for this command
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [FACE_EXTRACTION] - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'DEPRECATED: Use process_haar_extraction_jobs or process_dnn_extraction_jobs instead'

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
        parser.add_argument(
            '--method',
            type=str,
            choices=['haar', 'dnn', 'both'],
            default='both',
            help='Face extraction method to use'
        )

    def handle(self, *args, **options):
        max_jobs = options.get('max_jobs', 5)
        run_once = options.get('run_once', False)
        method = options.get('method', 'both')

        # Show deprecation warning
        self.stdout.write(
            self.style.WARNING(
                '⚠️  DEPRECATED: This command is deprecated. Use the new separate commands instead:'
            )
        )
        self.stdout.write('')
        self.stdout.write('For Haar Cascade face extraction:')
        self.stdout.write('  python manage.py process_haar_extraction_jobs')
        self.stdout.write('')
        self.stdout.write('For DNN face extraction:')
        self.stdout.write('  python manage.py process_dnn_extraction_jobs')
        self.stdout.write('')
        
        start_message = f'🔍 Starting DEPRECATED face extraction job processor (max_jobs: {max_jobs}, method: {method})'
        self.stdout.write(self.style.WARNING(start_message))
        logger.warning(start_message)        # Initialize Face Extraction service
        try:
            from django.core import management
            
            if method in ['haar', 'both']:
                self.stdout.write('Running Haar Cascade face extraction jobs...')
                management.call_command(
                    'process_haar_extraction_jobs',
                    max_jobs=max_jobs,
                    run_once=run_once
                )
            
            if method in ['dnn', 'both']:
                self.stdout.write('Running DNN face extraction jobs...')
                management.call_command(
                    'process_dnn_extraction_jobs',
                    max_jobs=max_jobs,
                    run_once=run_once
                )
                
        except Exception as e:
            error_message = f'❌ Face extraction delegation failed: {str(e)}'
            self.stdout.write(self.style.ERROR(error_message))
            logger.error(error_message, exc_info=True)
            return        # Command completed successfully
        completion_message = '✅ Delegated to appropriate face extraction commands'
        self.stdout.write(self.style.SUCCESS(completion_message))
        logger.info(completion_message)
        
        # Show completion message and recommend migration
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('📝 Migration Notice:'))
        self.stdout.write('For future use, please update your scripts to use the new commands directly.')
        self.stdout.write('This command will be removed in a future version.')
