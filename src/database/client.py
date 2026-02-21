from supabase import create_client, Client
from src.config import SUPABASE_URL, SUPABASE_SECRET_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
