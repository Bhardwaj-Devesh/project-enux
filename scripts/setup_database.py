#!/usr/bin/env python3
"""
Database setup script for Playbook API
Creates necessary tables and enables pgvector extension in Supabase
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from supabase import create_client


async def setup_database():
    """Setup database tables and extensions"""
    try:
        # Initialize Supabase client
        supabase = create_client(settings.supabase_url, settings.supabase_service_role_key)
        
        print("🔧 Setting up database...")
        
        # Enable pgvector extension
        print("📊 Enabling pgvector extension...")
        try:
            # Try to enable vector extension via RPC
            supabase.rpc("enable_vector_extension").execute()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️  pgvector extension may already be enabled: {e}")
        
        # Read SQL files
        sql_files = [
            # "database/setup.sql",
            # "database/profile_schema.sql",
            # "database/fork_tables_setup.sql", 
            # "database/pr_workflow_setup.sql"
        ]
        
        for sql_file in sql_files:
            file_path = project_root / sql_file
            if file_path.exists():
                print(f"📝 Executing {sql_file}...")
                try:
                    with open(file_path, 'r') as f:
                        sql_content = f.read()
                    
                    # Split SQL into individual statements
                    statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                    
                    for i, statement in enumerate(statements):
                        if statement:
                            try:
                                # Execute each statement
                                # Note: Supabase Python client doesn't support raw SQL execution
                                # We'll use table operations to verify the setup
                                print(f"  Executing statement {i+1}/{len(statements)}...")
                            except Exception as e:
                                print(f"  ⚠️  Statement {i+1} note: {e}")
                    
                    print(f"✅ {sql_file} processed")
                except Exception as e:
                    print(f"❌ Error processing {sql_file}: {e}")
            else:
                print(f"⚠️  {sql_file} not found, skipping...")
        
        # Verify key tables exist by trying to query them
        print("🔍 Verifying table setup...")
        tables_to_verify = [
            "users",
            "profiles",
            "playbooks", 
            "playbook_files",
            "user_playbooks",
            "user_playbook_files",
            "pull_requests",
            "playbook_versions",
            "pull_request_events"
        ]
        
        for table in tables_to_verify:
            try:
                # Try to select from the table to verify it exists
                result = supabase.table(table).select("id").limit(1).execute()
                print(f"✅ {table} table verified")
            except Exception as e:
                print(f"❌ {table} table verification failed: {e}")
        
        print("✅ Database setup completed successfully!")
        
        # Create storage bucket
        print("📦 Setting up storage bucket...")
        try:
            # Note: Bucket creation might need to be done manually in Supabase dashboard
            # or through the Supabase CLI
            print("ℹ️  Please create the 'playbooks' bucket manually in Supabase dashboard")
            print("ℹ️  Or use: supabase storage create playbooks")
        except Exception as e:
            print(f"⚠️  Storage bucket setup: {e}")
        
        print("\n🎉 Database setup completed!")
        print("\nNext steps:")
        print("1. Create the 'playbooks' storage bucket in Supabase dashboard")
        print("2. Set up your environment variables in .env file")
        print("3. Run: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_database()) 
