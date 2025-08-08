#!/usr/bin/env python3
"""
Database setup script for fork functionality
This script will help you set up the missing database tables for fork functionality
"""

import os
import sys

def print_setup_instructions():
    """Print setup instructions for the database"""
    
    print("🔧 Fork Functionality Database Setup Instructions")
    print("=" * 70)
    print()
    
    print("📋 Missing Database Components Found:")
    print("   1. user_playbooks table (for storing fork relationships)")
    print("   2. user_playbook_files table (for storing files in forks)")
    print("   3. playbook_files table (for original playbook files)")
    print("   4. Proper user registration (users table entries)")
    print()
    
    print("🚀 Setup Steps:")
    print()
    
    print("1️⃣ Open your Supabase Dashboard:")
    print("   - Go to https://supabase.com/dashboard")
    print("   - Select your project")
    print("   - Go to 'SQL Editor'")
    print()
    
    print("2️⃣ Run the main database setup (if not done already):")
    print("   - Copy and run the contents of: database/setup.sql")
    print("   - This creates users, playbooks, and file_vectors tables")
    print()
    
    print("3️⃣ Run the fork tables setup:")
    print("   - Copy and run the contents of: database/fork_tables_setup.sql")
    print("   - This creates user_playbooks, user_playbook_files, and playbook_files tables")
    print()
    
    print("4️⃣ Verify the tables exist:")
    print("   Run this query in SQL Editor:")
    print("   ```sql")
    print("   SELECT table_name FROM information_schema.tables")
    print("   WHERE table_schema = 'public'")
    print("   AND table_name IN ('users', 'playbooks', 'user_playbooks', 'user_playbook_files', 'playbook_files');")
    print("   ```")
    print()
    
    print("5️⃣ Expected tables after setup:")
    print("   ✅ users - User accounts")
    print("   ✅ playbooks - Original playbooks")
    print("   ✅ user_playbooks - Fork relationships")
    print("   ✅ user_playbook_files - Files in forks")
    print("   ✅ playbook_files - Files in original playbooks")
    print("   ✅ file_vectors - Vector embeddings for files")
    print()
    
    print("6️⃣ Test the setup:")
    print("   After running the SQL scripts, run:")
    print("   python test_complete_api_workflow.py")
    print()
    
    print("📄 SQL Scripts Location:")
    print("   - Main setup: database/setup.sql")
    print("   - Fork setup: database/fork_tables_setup.sql")
    print()

def check_current_status():
    """Check if we can connect to the API and test basic functionality"""
    
    print("🔍 Current Status Check")
    print("=" * 50)
    
    try:
        import requests
        
        # Test server health
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI server is running")
        else:
            print("❌ FastAPI server responded but with error")
    
    except requests.exceptions.ConnectionError:
        print("❌ FastAPI server is not running")
        print("   Start it with: python -m uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error checking server: {e}")
    
    print()
    
    # Check if environment variables are set
    try:
        from app.config import settings
        print("✅ Configuration loaded successfully")
        print(f"   Supabase URL: {settings.supabase_url}")
        print(f"   Storage bucket: {settings.storage_bucket_name}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    print()

def show_example_sql():
    """Show example SQL to check database status"""
    
    print("📊 Database Status Check Queries")
    print("=" * 50)
    print()
    
    print("Run these queries in your Supabase SQL Editor to check status:")
    print()
    
    print("1️⃣ Check if tables exist:")
    print("```sql")
    print("SELECT table_name FROM information_schema.tables")
    print("WHERE table_schema = 'public'")
    print("ORDER BY table_name;")
    print("```")
    print()
    
    print("2️⃣ Check users table:")
    print("```sql")
    print("SELECT COUNT(*) as user_count FROM users;")
    print("```")
    print()
    
    print("3️⃣ Check playbooks table:")
    print("```sql")
    print("SELECT COUNT(*) as playbook_count FROM playbooks;")
    print("```")
    print()
    
    print("4️⃣ Check if fork tables exist:")
    print("```sql")
    print("SELECT")
    print("  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_playbooks')")
    print("    THEN '✅ user_playbooks exists'")
    print("    ELSE '❌ user_playbooks missing' END as user_playbooks_status,")
    print("  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_playbook_files')")
    print("    THEN '✅ user_playbook_files exists'")
    print("    ELSE '❌ user_playbook_files missing' END as user_playbook_files_status,")
    print("  CASE WHEN EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'playbook_files')")
    print("    THEN '✅ playbook_files exists'")
    print("    ELSE '❌ playbook_files missing' END as playbook_files_status;")
    print("```")
    print()

if __name__ == "__main__":
    print("🚀 Fork Functionality Setup Helper")
    print("=" * 80)
    print()
    
    # Check current status
    check_current_status()
    
    # Show setup instructions
    print_setup_instructions()
    
    # Show example SQL
    show_example_sql()
    
    print("💡 Next Steps:")
    print("   1. Run the SQL scripts in your Supabase dashboard")
    print("   2. Test with: python test_complete_api_workflow.py")
    print("   3. Check the fork functionality")
    print()
    print("🎯 Goal: Complete end-to-end fork functionality testing")
    print("   Register → Login → Create Playbook → Fork → Verify")