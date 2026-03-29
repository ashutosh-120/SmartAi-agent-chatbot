import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load from backend/.env
load_dotenv('backend/.env')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    print("❌ Missing Supabase credentials")
    sys.exit(1)

supabase = create_client(url, key)

try:
    print("🔍 Checking 'analyses' table...")
    res = supabase.table("analyses").select("*").limit(1).execute()
    print("✅ Success! Columns found:")
    if res.data:
        for k in res.data[0].keys():
            print(f"  - {k}")
    else:
        print("  (Table is empty, cannot infer columns from data)")
except Exception as e:
    print(f"❌ Error querying table: {e}")
