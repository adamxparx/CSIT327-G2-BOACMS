import os
from django.core.management.base import BaseCommand
from accounts.utils import get_supabase_client
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Supabase connection'

    def handle(self, *args, **options):
        try:
            # Print environment variables for debugging
            self.stdout.write(f"SUPABASE_URL: {getattr(settings, 'SUPABASE_URL', 'Not set')}")
            self.stdout.write(f"SUPABASE_KEY: {'Set' if getattr(settings, 'SUPABASE_KEY', '') else 'Not set'}")
            
            supabase = get_supabase_client()
            self.stdout.write(
                self.style.SUCCESS('Successfully connected to Supabase!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to connect to Supabase: {str(e)}')
            )