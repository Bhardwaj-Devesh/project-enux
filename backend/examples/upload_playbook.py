#!/usr/bin/env python3
"""
Example script to upload a playbook using the Playbook API
Uses Google Gemini models for AI processing
"""

import requests
import json
import os
from pathlib import Path


def upload_playbook_example():
    """Example of uploading a playbook with files"""
    
    # API base URL
    base_url = "http://localhost:8000/api/v1"
    
    # First, register a user (if not exists)
    print("🔐 Registering user...")
    register_data = {
        "email": "demo@example.com",
        "password": "demo123456",
        "full_name": "Demo User"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    if response.status_code == 400 and "already exists" in response.text:
        print("✅ User already exists")
    elif response.status_code == 200:
        print("✅ User registered successfully")
    else:
        print(f"❌ Registration failed: {response.text}")
        return
    
    # Login to get access token
    print("🔑 Logging in...")
    login_data = {
        "email": "demo@example.com",
        "password": "demo123456"
    }
    
    response = requests.post(f"{base_url}/auth/login-json", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Create example files
    print("📝 Creating example files...")
    example_dir = Path("example_files")
    example_dir.mkdir(exist_ok=True)
    
    # Create a sample markdown file
    markdown_content = """
# GTM Strategy Playbook

## Overview
This playbook provides a comprehensive go-to-market strategy for early-stage startups.

## Key Components

### 1. Market Research
- Identify target market segments
- Analyze competitor landscape
- Understand customer pain points

### 2. Product Positioning
- Define unique value proposition
- Create positioning statement
- Develop messaging framework

### 3. Channel Strategy
- Direct sales approach
- Digital marketing channels
- Partnership opportunities

### 4. Revenue Model
- Pricing strategy
- Sales process
- Customer acquisition cost

## Implementation Timeline
- Month 1-2: Market research and positioning
- Month 3-4: Channel setup and testing
- Month 5-6: Full launch and optimization

## Success Metrics
- Customer acquisition rate
- Revenue growth
- Market share
- Customer satisfaction
"""
    
    with open(example_dir / "GTM_Strategy.md", "w") as f:
        f.write(markdown_content)
    
    # Create a sample CSV file
    csv_content = """Metric,Target,Current,Status
Customer Acquisition Cost,$50,$75,Needs Improvement
Conversion Rate,5%,3.2%,Below Target
Monthly Recurring Revenue,$10K,$8.5K,On Track
Customer Lifetime Value,$500,$450,Below Target
Churn Rate,5%,7%,Needs Attention"""
    
    with open(example_dir / "metrics.csv", "w") as f:
        f.write(csv_content)
    
    # Create a sample JSON file
    json_content = {
        "playbook_info": {
            "title": "GTM Strategy v1",
            "version": "1.0",
            "author": "Demo User",
            "created_date": "2024-01-15",
            "tags": ["GTM", "marketing", "strategy", "startup"]
        },
        "target_audience": {
            "primary": "Early-stage SaaS startups",
            "secondary": "B2B companies with $1M-$10M ARR"
        },
        "key_phases": [
            "Market Research",
            "Product Positioning", 
            "Channel Strategy",
            "Revenue Optimization"
        ]
    }
    
    with open(example_dir / "playbook_config.json", "w") as f:
        json.dump(json_content, f, indent=2)
    
    print("✅ Example files created")
    
    # Upload playbook
    print("📤 Uploading playbook...")
    print("🤖 AI processing will be handled by Google Gemini models...")
    
    files = [
        ("files", open(example_dir / "GTM_Strategy.md", "rb")),
        ("files", open(example_dir / "metrics.csv", "rb")),
        ("files", open(example_dir / "playbook_config.json", "rb"))
    ]
    
    data = {
        "title": "GTM Strategy v1",
        "description": "Comprehensive go-to-market strategy for early-stage startups with focus on market research, positioning, and channel strategy.",
        "stage": "pre-seed",
        "tags": json.dumps(["GTM", "marketing", "strategy", "startup"]),
        "version": "v1"
    }
    
    response = requests.post(
        f"{base_url}/playbooks/upload",
        headers=headers,
        data=data,
        files=files
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Playbook uploaded successfully!")
        print(f"📚 Playbook ID: {result['playbook']['id']}")
        print(f"📊 Processing Status: {result['processing_status']}")
        print(f"📝 Message: {result['message']}")
        
        # Get processing status
        playbook_id = result['playbook']['id']
        print(f"\n🔄 Checking processing status...")
        
        status_response = requests.get(
            f"{base_url}/playbooks/{playbook_id}/status",
            headers=headers
        )
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"📊 Status: {status['status']}")
            print(f"📝 Message: {status['message']}")
            if status.get('summary'):
                print(f"📋 Summary (Generated by Gemini): {status['summary'][:200]}...")
            if status.get('extracted_tags'):
                print(f"🏷️  Tags (Extracted by Gemini): {status['extracted_tags']}")
    
    else:
        print(f"❌ Upload failed: {response.text}")
    
    # Clean up example files
    print("\n🧹 Cleaning up example files...")
    for file in example_dir.glob("*"):
        file.unlink()
    example_dir.rmdir()
    print("✅ Cleanup completed")


if __name__ == "__main__":
    print("🚀 Playbook Upload Example")
    print("🤖 Using Google Gemini for AI processing")
    print("=" * 50)
    upload_playbook_example() 
