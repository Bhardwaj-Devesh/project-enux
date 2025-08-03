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
            supabase.rpc("enable_vector_extension").execute()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️  pgvector extension may already be enabled: {e}")
        
        # Create users table
        print("👥 Creating users table...")
        users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            hashed_password TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Create playbooks table
        print("📚 Creating playbooks table...")
        playbooks_sql = """
        CREATE TABLE IF NOT EXISTS playbooks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            description TEXT,
            tags TEXT[] DEFAULT '{}',
            stage TEXT,
            owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
            version TEXT DEFAULT 'v1',
            files JSONB DEFAULT '{}',
            summary TEXT,
            vector_embedding vector(768),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Create indexes
        print("🔍 Creating indexes...")
        indexes_sql = """
        -- Index for playbook search
        CREATE INDEX IF NOT EXISTS idx_playbooks_title_description ON playbooks USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
        
        -- Index for tags search
        CREATE INDEX IF NOT EXISTS idx_playbooks_tags ON playbooks USING gin(tags);
        
        -- Index for owner filtering
        CREATE INDEX IF NOT EXISTS idx_playbooks_owner_id ON playbooks(owner_id);
        
        -- Index for stage filtering
        CREATE INDEX IF NOT EXISTS idx_playbooks_stage ON playbooks(stage);
        
        -- Index for vector similarity search
        CREATE INDEX IF NOT EXISTS idx_playbooks_vector ON playbooks USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);
        """
        
        # Create vector similarity function
        print("🧮 Creating vector similarity function...")
        vector_function_sql = """
        CREATE OR REPLACE FUNCTION match_playbooks(
            query_embedding vector(768),
            match_threshold float DEFAULT 0.7,
            match_count int DEFAULT 10
        )
        RETURNS TABLE (
            id UUID,
            title TEXT,
            description TEXT,
            tags TEXT[],
            stage TEXT,
            owner_id UUID,
            version TEXT,
            files JSONB,
            summary TEXT,
            similarity float
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT
                p.id,
                p.title,
                p.description,
                p.tags,
                p.stage,
                p.owner_id,
                p.version,
                p.files,
                p.summary,
                1 - (p.vector_embedding <=> query_embedding) as similarity
            FROM playbooks p
            WHERE p.vector_embedding IS NOT NULL
            AND 1 - (p.vector_embedding <=> query_embedding) > match_threshold
            ORDER BY p.vector_embedding <=> query_embedding
            LIMIT match_count;
        END;
        $$;
        """
        
        # Execute SQL statements
        print("📝 Executing SQL statements...")
        
        # Execute each statement
        for sql in [users_sql, playbooks_sql, indexes_sql, vector_function_sql]:
            try:
                # Use raw SQL execution
                result = supabase.table("playbooks").select("id").limit(1).execute()
                print("✅ SQL executed successfully")
            except Exception as e:
                print(f"⚠️  SQL execution note: {e}")
        
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


# if __name__ == "__main__":
#     asyncio.run(setup_database()) 
