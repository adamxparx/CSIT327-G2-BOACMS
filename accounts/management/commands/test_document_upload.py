import os
from django.core.management.base import BaseCommand
from accounts.utils import upload_document_to_supabase
from django.conf import settings


class Command(BaseCommand):
    help = 'Test document upload to Supabase'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the file to upload')
        parser.add_argument('resident_id', type=int, help='Resident ID for the upload')

    def handle(self, *args, **options):
        file_path = options['file_path']
        resident_id = options['resident_id']
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
            
        try:
            # Create a simple file-like object
            class SimpleFile:
                def __init__(self, path):
                    self.name = os.path.basename(path)
                    self.content_type = 'image/jpeg' if path.lower().endswith('.jpg') or path.lower().endswith('.jpeg') else 'application/pdf'
                    with open(path, 'rb') as f:
                        self.data = f.read()
                
                def read(self):
                    return self.data
                    
            file_obj = SimpleFile(file_path)
            
            # Upload the document
            url = upload_document_to_supabase(file_obj, resident_id)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully uploaded document! URL: {url}')
            )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to upload document: {str(e)}')
            )