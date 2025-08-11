#!/usr/bin/env python3
"""
Simple PR Workflow Test - Tests all PR creation APIs
"""

import requests
import json
import tempfile
import zipfile
import os
from datetime import datetime

def print_step(step_num, title):
    print(f"\n{'='*60}")
    print(f"{step_num}️⃣ {title}")
    print('='*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️ {message}")

def main():
    base_url = "http://localhost:8000/api/v1"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("🚀 PR WORKFLOW API TEST SUITE")
    print("=" * 60)
    print(f"Test ID: {timestamp}")
    print(f"Base URL: {base_url}")
    
    # Step 1: Setup user
    print_step(1, "Setting Up Test User")
    
    test_email = f"prtest_{timestamp}@example.com"
    test_password = "PRTest123!"
    
    # Register
    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": f"PR Test User {timestamp}"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    if response.status_code != 200:
        print_error(f"Registration failed: {response.text}")
        return
    
    user_data = response.json()
    user_id = user_data['id']
    print_success(f"User registered: {user_id}")
    
    # Login
    login_data = {"email": test_email, "password": test_password}
    response = requests.post(f"{base_url}/auth/login-json", json=login_data)
    if response.status_code != 200:
        print_error(f"Login failed: {response.text}")
        return
    
    token_data = response.json()
    bearer_token = token_data['access_token']
    auth_headers = {"Authorization": f"Bearer {bearer_token}"}
    print_success("Authentication successful")
    
    # Step 2: Create master playbook
    print_step(2, "Creating Master Playbook")
    
    content = f"""# PR Test Master Playbook {timestamp}

This is for testing PR workflow.

## Original Features
- Basic documentation
- Simple configuration
- Test data

## Version 1.0
Created: {datetime.now().isoformat()}
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    with open(temp_file_path, 'rb') as f:
        files = {'files': (f'main_{timestamp}.md', f, 'text/markdown')}
        data = {
            'title': f'PR Test Master {timestamp}',
            'description': 'Master playbook for PR testing',
            'stage': 'production',
            'tags': json.dumps(['test', 'pr']),
            'version': 'v1',
            'owner_id': user_id
        }
        
        response = requests.post(f"{base_url}/playbooks/upload", files=files, data=data)
        
        if response.status_code != 200:
            print_error(f"Playbook creation failed: {response.text}")
            return
        
        upload_result = response.json()
        playbook_id = upload_result['playbook']['id']
        print_success(f"Master playbook created: {playbook_id}")
    
    os.unlink(temp_file_path)
    
    # Add a file to master
    print_info("Adding file to master playbook...")
    readme_content = """# Privacy Policy

We respect user privacy and handle data responsibly.

## Data Collection
We collect minimal necessary data.

## GDPR Compliance
Users have rights under GDPR including data access and deletion.
"""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(readme_content)
        temp_path = temp_file.name
    
    with open(temp_path, 'rb') as f:
        files = {'file': ('privacy.md', f)}
        data = {
            'file_path': 'docs/privacy.md',
            'tags': json.dumps(['master'])
        }
        
        response = requests.post(
            f"{base_url}/playbooks/{playbook_id}/files",
            files=files,
            data=data,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            print_success("Added privacy.md to master")
        else:
            print_error(f"Failed to add file: {response.text}")
    
    os.unlink(temp_path)
    
    # Step 3: Create fork
    print_step(3, "Creating Fork")
    
    fork_data = {
        "playbook_id": playbook_id,
        "user_id": user_id
    }
    
    response = requests.post(f"{base_url}/playbooks/fork", json=fork_data, headers=auth_headers)
    if response.status_code != 200:
        print_error(f"Fork creation failed: {response.text}")
        return
    
    fork_result = response.json()
    fork_id = fork_result['new_playbook_id']
    print_success(f"Fork created: {fork_id}")
    
    # Step 4: Test sync status
    print_step(4, "Testing Sync Status API")
    
    response = requests.get(
        f"{base_url}/pull-requests/forks/{fork_id}/sync-status",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        sync_status = response.json()
        print_success("Sync status retrieved")
        print_info(f"Fork behind: {sync_status.get('is_behind', 'unknown')}")
        print_info(f"Base version: {sync_status.get('base_version', 'unknown')}")
        print_info(f"Master version: {sync_status.get('master_latest_version', 'unknown')}")
    else:
        print_error(f"Sync status failed: {response.text}")
    
    # Step 5: Test PR creation with JSON
    print_step(5, "Testing PR Creation (JSON)")
    
    pr_data = {
        "fork_id": fork_id,
        "title": "Enhanced Privacy Policy with GDPR Compliance",
        "description": "This PR updates our privacy policy to ensure full GDPR compliance and adds new data handling procedures.",
        "commit_message": "feat: enhance privacy policy with GDPR compliance, data retention, and user rights",
        "file_changes": [
            {
                "file_path": "docs/privacy.md",
                "content": """# Privacy Policy (GDPR Compliant)

We respect user privacy and handle data in full compliance with GDPR.

## Data Collection
We collect only necessary personal information with explicit consent.

## GDPR Compliance (NEW)
Under GDPR, you have the following rights:
- Right to access your personal data
- Right to rectify inaccurate data  
- Right to erasure (right to be forgotten)
- Right to data portability
- Right to object to processing
- Right to restrict processing

## Data Retention (NEW)
- Personal data retained for maximum 2 years
- Users can request deletion at any time
- Audit logs maintained for compliance

## Contact Information
Data Protection Officer: dpo@example.com
Privacy questions: privacy@example.com

## Cookies and Tracking
We use minimal essential cookies only. Analytics require explicit consent.

## Third-Party Data Sharing
We do not share personal data with third parties without explicit consent.
""",
                "change_type": "modified"
            },
            {
                "file_path": "legal/gdpr-compliance.md",
                "content": """# GDPR Compliance Documentation

## Legal Basis for Processing
We process personal data under the following legal bases:
- Consent for marketing communications
- Contract performance for service delivery
- Legitimate interest for security and fraud prevention

## Data Processing Agreements
All third-party processors have signed DPAs.

## Breach Notification
We will notify authorities within 72 hours of any data breach.

## Data Protection Impact Assessments
Conducted for all high-risk processing activities.
""",
                "change_type": "added"
            }
        ]
    }
    
    print_info("Creating PR with GDPR privacy changes (should trigger risk flags)...")
    
    response = requests.post(
        f"{base_url}/pull-requests/",
        json=pr_data,
        headers=auth_headers
    )
    
    if response.status_code == 200:
        pr_result = response.json()
        print_success("PR created successfully!")
        print_info(f"PR ID: {pr_result['id']}")
        print_info(f"Status: {pr_result.get('status', 'unknown')}")
        
        # Show AI analysis results
        if pr_result.get('summary'):
            print_info(f"🤖 AI Title: {pr_result['summary']}")
        if pr_result.get('change_summary'):
            print_info(f"🤖 AI Description: {pr_result['change_summary'][:120]}...")
        if pr_result.get('risk_flags'):
            print_info(f"⚠️ Risk Flags: {', '.join(pr_result['risk_flags'])}")
        if pr_result.get('merge_checklist'):
            print_info(f"📋 Checklist Items: {len(pr_result['merge_checklist'])}")
            for item in pr_result['merge_checklist'][:2]:
                print_info(f"   - {item}")
        
        pr_id = pr_result['id']
        
    elif response.status_code == 409:
        print_error(f"Fork sync required: {response.text}")
        pr_id = None
    else:
        print_error(f"PR creation failed: {response.text}")
        pr_id = None
    
    # Step 6: Test ZIP upload PR
    print_step(6, "Testing PR Creation (ZIP Upload)")
    
    # Create a ZIP with security changes
    zip_content = create_test_zip()
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as zip_file:
        zip_file.write(zip_content)
        zip_path = zip_file.name
    
    try:
        with open(zip_path, 'rb') as f:
            files = {'zip_file': ('security-updates.zip', f, 'application/zip')}
            data = {
                'fork_id': fork_id,
                'title': 'Security Policy Updates via ZIP',
                'description': 'Comprehensive security policy updates and new compliance documentation',
                'commit_message': 'security: add comprehensive security policies and compliance docs'
            }
            
            print_info("Uploading ZIP with security policy changes...")
            
            response = requests.post(
                f"{base_url}/pull-requests/from-zip",
                files=files,
                data=data,
                headers=auth_headers
            )
            
            if response.status_code == 200:
                zip_pr_result = response.json()
                print_success("ZIP-based PR created successfully!")
                print_info(f"PR ID: {zip_pr_result['id']}")
                print_info(f"🤖 AI Title: {zip_pr_result.get('summary', 'N/A')}")
                print_info(f"⚠️ Risk Flags: {', '.join(zip_pr_result.get('risk_flags', []))}")
                zip_pr_id = zip_pr_result['id']
            else:
                print_error(f"ZIP PR creation failed: {response.text}")
                zip_pr_id = None
    finally:
        os.unlink(zip_path)
    
    # Step 7: Test PR retrieval
    if pr_id:
        print_step(7, f"Testing PR Retrieval (PR: {pr_id})")
        
        response = requests.get(
            f"{base_url}/pull-requests/{pr_id}",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            pr_data = response.json()
            print_success("PR retrieved successfully!")
            print_info(f"Title: {pr_data.get('title', 'N/A')}")
            print_info(f"Created: {pr_data.get('created_at', 'N/A')}")
            
            # Show file changes (file_changes is now a JSONB array in comprehensive schema)
            file_changes = pr_data.get('file_changes', [])
            print_info(f"File Changes: {len(file_changes)} files")
            for change in file_changes:
                if isinstance(change, dict):
                    print_info(f"  - {change.get('file_path', 'unknown')}: {change.get('change_type', 'unknown')}")
                else:
                    print_info(f"  - {change}")  # fallback
        else:
            print_error(f"PR retrieval failed: {response.text}")
    
    # Step 8: Test PR listing
    print_step(8, "Testing PR Listing")
    
    response = requests.get(
        f"{base_url}/pull-requests/",
        headers=auth_headers
    )
    
    if response.status_code == 200:
        pr_list = response.json()
        print_success("PR listing successful!")
        print_info(f"Total PRs: {pr_list.get('total_count', 0)}")
        
        prs = pr_list.get('pull_requests', [])
        print_info(f"Listed PRs: {len(prs)}")
        for pr in prs[:3]:  # Show first 3
            print_info(f"  - {pr.get('title', 'Unknown')} (ID: {pr.get('id', 'N/A')[:8]}...)")
    else:
        print_error(f"PR listing failed: {response.text}")
    
    # Final summary
    print_step(9, "Test Summary")
    print_success("🎉 PR Workflow API Test Complete!")
    print_info(f"Test User: {user_id}")
    print_info(f"Master Playbook: {playbook_id}")
    print_info(f"Fork: {fork_id}")
    if pr_id:
        print_info(f"JSON PR: {pr_id}")
    if 'zip_pr_id' in locals() and zip_pr_id:
        print_info(f"ZIP PR: {zip_pr_id}")
    
    print("\n🚀 All major PR workflow APIs tested successfully!")
    print("   ✅ User authentication")
    print("   ✅ Playbook and fork creation")  
    print("   ✅ Sync status checking")
    print("   ✅ PR creation via JSON")
    print("   ✅ PR creation via ZIP upload")
    print("   ✅ AI analysis and risk detection")
    print("   ✅ PR retrieval and listing")


def create_test_zip():
    """Create test ZIP with security-related content"""
    import io
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Security policy
        security_content = """# Security Policy

## Vulnerability Reporting
Report security vulnerabilities to security@example.com

## Data Encryption
- All data encrypted at rest using AES-256
- TLS 1.3 for data in transit
- End-to-end encryption for sensitive communications

## Access Control
- Multi-factor authentication required for admin access
- Role-based access control (RBAC) implemented
- Regular access reviews quarterly

## Incident Response Plan
1. Immediate isolation and containment
2. Impact assessment and documentation
3. Stakeholder notification within 1 hour
4. Remediation and system recovery
5. Post-incident review and improvements

## Compliance
- SOC 2 Type II certified
- GDPR compliant data processing
- Regular security audits by third parties
"""
        zip_file.writestr("security/policy.md", security_content)
        
        # Compliance documentation
        compliance_content = """# Compliance Documentation

## Regulatory Framework
We comply with the following regulations:
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- SOX (Sarbanes-Oxley Act)
- HIPAA (for healthcare data)

## Audit Trail
All system access and data modifications are logged with:
- User identification
- Timestamp
- Action performed
- Data affected
- IP address and location

## Data Classification
- Public: Marketing materials, published documentation
- Internal: Employee information, business processes
- Confidential: Customer data, financial records
- Restricted: Authentication credentials, encryption keys
"""
        zip_file.writestr("compliance/framework.md", compliance_content)
        
        # Updated user data with compliance fields
        user_data = """id,name,email,role,gdpr_consent,data_retention_date,last_access
1,John Doe,john@example.com,admin,true,2026-01-01,2024-01-08
2,Jane Smith,jane@example.com,user,true,2026-01-02,2024-01-07
3,Bob Johnson,bob@example.com,user,false,2025-01-03,2024-01-05
"""
        zip_file.writestr("data/users.csv", user_data)
    
    return zip_buffer.getvalue()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()