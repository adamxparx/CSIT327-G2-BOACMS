import os
from supabase import create_client, Client
from django.conf import settings

# Supabase configuration
SUPABASE_URL = getattr(settings, 'SUPABASE_URL', '')
SUPABASE_KEY = getattr(settings, 'SUPABASE_KEY', '')
DOCUMENTS_BUCKET = "documents_images"

def get_supabase_client() -> Client:
    """Create and return a Supabase client instance."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in Django settings")
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)