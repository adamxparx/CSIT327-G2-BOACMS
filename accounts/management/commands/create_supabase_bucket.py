from django.core.management.base import BaseCommand
from accounts.utils import get_supabase_client


class Command(BaseCommand):
    help = 'Create the documents_images bucket in Supabase'

    def handle(self, *args, **options):
        try:
            supabase = get_supabase_client()
            
            # Create the bucket
            response = supabase.storage.create_bucket("documents_images")
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created bucket "documents_images"!')
            )
            
            # Set the bucket to public
            supabase.storage.update_bucket("documents_images", {
                "public": True
            })
            
            self.stdout.write(
                self.style.SUCCESS('Set bucket "documents_images" to public!')
            )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create bucket: {str(e)}')
            )