#!/usr/bin/env python3
"""
Setup comprehensive PR schema in database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_comprehensive_schema():
    """Set up the comprehensive PR schema"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Missing Supabase credentials")
        print("Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set in your .env file")
        return False
    
    print("🚀 SETTING UP COMPREHENSIVE PR SCHEMA")
    print("="*50)
    
    print("📌 The comprehensive schema includes:")
    print("   - target_playbook_id, title, description, commit_message")
    print("   - risk_flags, merge_checklist arrays")
    print("   - updated_at, merged_at, closed_at timestamps")
    print("   - Enhanced pull_request_files with change_type, risk_flags, confidence")
    
    print("\n💡 To set up the schema:")
    print("1. Go to Supabase Dashboard > SQL Editor")
    print("2. Copy the content from: database/pr_workflow_setup.sql")
    print("3. Run the SQL script")
    
    print("\n✅ After running the SQL, test with:")
    print("   python test_pr_workflow_simple.py")
    
    return True

if __name__ == "__main__":
    setup_comprehensive_schema()