import os
import uuid
from django.conf import settings
from supabase import Client
from .supabase_config import get_supabase_client, DOCUMENTS_BUCKET


def upload_document_to_supabase(document_file, resident_id: int) -> str:
    """
    Upload a document file to Supabase storage and return the public URL.
    
    Args:
        document_file: The file object to upload
        resident_id: The ID of the resident (used for organizing files)
        
    Returns:
        str: The public URL of the uploaded file
        
    Raises:
        Exception: If the upload fails
    """
    try:
        # Get Supabase client
        supabase: Client = get_supabase_client()
        
        # Generate a unique filename to prevent conflicts
        file_extension = os.path.splitext(document_file.name)[1]
        unique_filename = f"{resident_id}_{uuid.uuid4().hex}{file_extension}"
        
        # Define the path in the bucket
        file_path = f"address_documents/{unique_filename}"
        
        # Upload the file
        response = supabase.storage.from_(DOCUMENTS_BUCKET).upload(
            path=file_path,
            file=document_file.read(),
            file_options={"content-type": document_file.content_type}
        )
        
        # Get the public URL
        public_url = supabase.storage.from_(DOCUMENTS_BUCKET).get_public_url(file_path)
        
        return public_url
        
    except Exception as e:
        raise Exception(f"Failed to upload document to Supabase: {str(e)}")


def delete_document_from_supabase(file_url: str) -> bool:
    """
    Delete a document from Supabase storage.
    
    Args:
        file_url: The public URL of the file to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        # Get Supabase client
        supabase: Client = get_supabase_client()
        
        # Extract the file path from the URL
        # Assuming the URL format: https://<project>.supabase.co/storage/v1/object/public/<bucket>/<path>
        if "public/" in file_url:
            file_path = file_url.split("public/")[-1]
            bucket_name = file_path.split("/")[0]
            file_path = "/".join(file_path.split("/")[1:])
            
            # Delete the file
            response = supabase.storage.from_(bucket_name).remove([file_path])
            return True
            
        return False
        
    except Exception as e:
        print(f"Failed to delete document from Supabase: {str(e)}")
        return False