from django.core.management.base import BaseCommand
from django.core import management
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manage the job scheduler and manually trigger scheduled jobs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['status', 'start', 'stop', 'trigger_face_extraction', 'trigger_tagging', 'trigger_all'],
            default='status',
            help='Action to perform'
        )
        parser.add_argument(
            '--max-jobs',
            type=int,
            help='Maximum number of jobs to process (for trigger actions)'
        )

    def handle(self, *args, **options):
        action = options.get('action', 'status')
        max_jobs = options.get('max_jobs')

        if action == 'status':
            self._show_status()
        elif action == 'start':
            self._start_scheduler()
        elif action == 'stop':
            self._stop_scheduler()
        elif action == 'trigger_face_extraction':
            self._trigger_face_extraction(max_jobs)
        elif action == 'trigger_tagging':
            self._trigger_tagging(max_jobs)
        elif action == 'trigger_all':
            self._trigger_all_jobs(max_jobs)

    def _show_status(self):
        """Show scheduler status and job information"""
        self.stdout.write(self.style.SUCCESS('=== Job Scheduler Status ==='))
        
        try:
            from jobs.scheduler import is_running, get_scheduler
            
            if is_running():
                self.stdout.write(self.style.SUCCESS('📅 Scheduler Status: RUNNING'))
                
                scheduler = get_scheduler()
                jobs = scheduler.get_jobs()
                if jobs:
                    self.stdout.write(f'\n📋 Scheduled Jobs ({len(jobs)}):')
                    for job in jobs:
                        next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'Not scheduled'
                        self.stdout.write(f'  • {job.id}: Next run at {next_run}')
                else:
                    self.stdout.write('📋 No jobs scheduled')
            else:
                self.stdout.write(self.style.WARNING('📅 Scheduler Status: NOT RUNNING'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error checking scheduler status: {e}'))

    def _start_scheduler(self):
        """Start the scheduler"""
        try:
            from jobs import scheduler
            scheduler.start()
            self.stdout.write(self.style.SUCCESS('✅ Scheduler started successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to start scheduler: {e}'))

    def _stop_scheduler(self):
        """Stop the scheduler"""
        try:
            from jobs import scheduler
            scheduler.stop()
            self.stdout.write(self.style.SUCCESS('✅ Scheduler stopped successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to stop scheduler: {e}'))

    def _trigger_face_extraction(self, max_jobs=None):
        """Manually trigger face extraction jobs"""
        self.stdout.write('🔍 Triggering face extraction jobs...')
        try:
            kwargs = {'run_once': True}
            if max_jobs:
                kwargs['max_jobs'] = max_jobs
            
            management.call_command('process_face_extraction_jobs', **kwargs)
            self.stdout.write(self.style.SUCCESS('✅ Face extraction jobs triggered'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to trigger face extraction jobs: {e}'))

    def _trigger_tagging(self, max_jobs=None):
        """Manually trigger tagging jobs"""
        self.stdout.write('🏷️  Triggering tagging jobs...')
        try:
            kwargs = {'run_once': True}
            if max_jobs:
                kwargs['max_jobs'] = max_jobs
            
            management.call_command('process_tagging_jobs', **kwargs)
            self.stdout.write(self.style.SUCCESS('✅ Tagging jobs triggered'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to trigger tagging jobs: {e}'))

    def _trigger_all_jobs(self, max_jobs=None):
        """Manually trigger all scheduled jobs"""
        self.stdout.write('🚀 Triggering all scheduled jobs...')
        self._trigger_face_extraction(max_jobs)
        self._trigger_tagging(max_jobs)
        self.stdout.write(self.style.SUCCESS('✅ All jobs triggered'))
