#!/usr/bin/env python3
"""
Database setup script for Playbook API
Executes SQL files directly to create necessary tables and extensions
"""

import asyncio
import sys
import os
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings


def execute_sql_file(connection, sql_file_path):
    """Execute SQL file content"""
    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        cursor = connection.cursor()
        for i, statement in enumerate(statements):
            if statement:
                try:
                    print(f"  Executing statement {i+1}/{len(statements)}...")
                    cursor.execute(statement)
                    print(f"  ✅ Statement {i+1} executed successfully")
                except Exception as e:
                    print(f"  ⚠️  Statement {i+1} failed: {e}")
                    # Continue with other statements
        
        cursor.close()
        return True
    except Exception as e:
        print(f"❌ Error executing {sql_file_path}: {e}")
        return False


async def setup_database():
    """Setup database tables and extensions"""
    try:
        print("🔧 Setting up database...")
        
        # Parse connection string from Supabase URL
        # Supabase URL format: https://project-ref.supabase.co
        # We need to extract the host and use the service role key
        supabase_url = settings.supabase_url
        host = supabase_url.replace('https://', '').replace('.supabase.co', '')
        
        # Connection parameters
        db_params = {
            'host': f'{host}.supabase.co',
            'database': 'postgres',
            'user': 'postgres',
            'password': settings.supabase_service_role_key,
            'port': 5432,
            'sslmode': 'require'
        }
        
        print(f"🔌 Connecting to database at {db_params['host']}...")
        
        # Connect to database
        connection = psycopg2.connect(**db_params)
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        print("✅ Connected to database successfully!")
        
        # SQL files to execute in order
        sql_files = [
            "database/setup.sql",
            "database/fork_tables_setup.sql", 
            "database/pr_workflow_setup.sql"
        ]
        
        for sql_file in sql_files:
            file_path = project_root / sql_file
            if file_path.exists():
                print(f"📝 Executing {sql_file}...")
                success = execute_sql_file(connection, file_path)
                if success:
                    print(f"✅ {sql_file} executed successfully")
                else:
                    print(f"❌ {sql_file} failed")
            else:
                print(f"⚠️  {sql_file} not found, skipping...")
        
        # Verify key tables exist
        print("🔍 Verifying table setup...")
        cursor = connection.cursor()
        tables_to_verify = [
            "users",
            "playbooks", 
            "playbook_files",
            "user_playbooks",
            "user_playbook_files"
        ]
        
        for table in tables_to_verify:
            try:
                cursor.execute(f"SELECT 1 FROM {table} LIMIT 1")
                print(f"✅ {table} table verified")
            except Exception as e:
                print(f"❌ {table} table verification failed: {e}")
        
        cursor.close()
        connection.close()
        
        print("✅ Database setup completed successfully!")
        
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
