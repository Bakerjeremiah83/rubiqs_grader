# app/supabase_client.py
import os

try:
    from supabase import create_client
except ImportError:
    create_client = None

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"⚠️ Could not initialize Supabase client: {e}")
else:
    if not create_client:
        print("⚠️ 'supabase' package not installed (pip install supabase)")
    else:
        print("⚠️ Missing SUPABASE_URL or key; Supabase client not created")


def upload_to_supabase(bucket: str, path: str, bytes_data: bytes,
                       content_type: str = "application/octet-stream",
                       upsert: bool = True) -> str:
    """
    Upload bytes to Supabase Storage and return a public URL.
    """
    if supabase is None:
        raise RuntimeError("Supabase client not configured")

    supabase.storage.from_(bucket).upload(
        path,
        bytes_data,
        {"content-type": content_type, "upsert": upsert},
    )

    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
