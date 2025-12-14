from django.core.management.base import BaseCommand
from accounts.utils import get_supabase_client


class Command(BaseCommand):
    help = 'Check if the documents_images bucket exists in Supabase'

    def handle(self, *args, **options):
        try:
            supabase = get_supabase_client()
            
            # List all buckets
            response = supabase.storage.list_buckets()
            buckets = response
            
            self.stdout.write(f"Available buckets: {[bucket.name for bucket in buckets]}")
            
            # Check if our bucket exists
            bucket_names = [bucket.name for bucket in buckets]
            if "documents_images" in bucket_names:
                self.stdout.write(
                    self.style.SUCCESS('Bucket "documents_images" exists!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Bucket "documents_images" does not exist.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to check buckets: {str(e)}')
            )