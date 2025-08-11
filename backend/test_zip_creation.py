#!/usr/bin/env python3
"""
Simple test to verify ZIP file creation and saving
"""

import requests
import json
import tempfile
import os
from datetime import datetime

def test_zip_creation():
    """Test ZIP creation with proper file saving"""
    
    print("🧪 ZIP File Creation Test")
    print("=" * 40)
    
    base_url = "http://localhost:8000/api/v1"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Setup user
    test_email = f"ziptest_{timestamp}@example.com"
    test_password = "ZipTest123!"
    
    print("1️⃣ Setting up user...")
    # Register and login
    register_data = {
        "email": test_email,
        "password": test_password,
        "full_name": f"ZIP Test User {timestamp}"
    }
    
    response = requests.post(f"{base_url}/auth/register", json=register_data)
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return
    
    user_data = response.json()
    user_id = user_data['id']
    print(f"✅ User: {user_id}")
    
    login_data = {"email": test_email, "password": test_password}
    response = requests.post(f"{base_url}/auth/login-json", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token_data = response.json()
    bearer_token = token_data['access_token']
    auth_headers = {"Authorization": f"Bearer {bearer_token}"}
    print(f"✅ Authentication successful")
    
    print("\n2️⃣ Creating playbook...")
    # Create playbook
    content = f"# ZIP Test Playbook {timestamp}\n\nThis is a test playbook for ZIP creation verification."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    with open(temp_file_path, 'rb') as f:
        files = {'files': (f'test_{timestamp}.md', f, 'text/markdown')}
        data = {
            'title': f'ZIP Test {timestamp}',
            'description': 'ZIP creation test playbook',
            'stage': 'testing',
            'tags': json.dumps(['test', 'zip']),
            'version': 'v1',
            'owner_id': user_id
        }
        
        response = requests.post(f"{base_url}/playbooks/upload", files=files, data=data)
        if response.status_code != 200:
            print(f"❌ Playbook creation failed: {response.text}")
            return
        
        upload_result = response.json()
        playbook_id = upload_result['playbook']['id']
        print(f"✅ Playbook created: {playbook_id}")
    
    os.unlink(temp_file_path)
    
    print("\n3️⃣ Uploading test files...")
    # Upload a few test files with allowed types
    test_files = [
        {
            "name": "readme.md",
            "content": "# README\n\nThis is a test README file.",
            "type": "md"
        },
        {
            "name": "data.csv", 
            "content": "name,value\ntest1,100\ntest2,200\n",
            "type": "csv"
        },
        {
            "name": "script.txt",  # Using .txt for Python content to avoid constraint
            "content": "#!/usr/bin/env python3\nprint('Hello from test script!')\n",
            "type": "txt"
        }
    ]
    
    uploaded_count = 0
    for file_info in test_files:
        print(f"📤 Uploading: {file_info['name']}")
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(file_info['content'])
            temp_path = temp_file.name
        
        try:
            with open(temp_path, 'rb') as f:
                files = {'file': (file_info['name'], f)}
                data = {
                    'file_path': file_info['name'],
                    'tags': json.dumps(['test'])
                }
                
                response = requests.post(
                    f"{base_url}/playbooks/{playbook_id}/files",
                    files=files,
                    data=data,
                    headers=auth_headers
                )
                
                if response.status_code == 200:
                    uploaded_count += 1
                    print(f"   ✅ Uploaded successfully")
                else:
                    print(f"   ❌ Upload failed: {response.text}")
        
        finally:
            os.unlink(temp_path)
    
    print(f"📄 Total files uploaded: {uploaded_count}")
    
    print("\n4️⃣ Testing download and ZIP creation...")
    # Test download
    response = requests.get(f"{base_url}/playbooks/{playbook_id}/download", headers=auth_headers)
    print(f"Download Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ Download successful!")
        print(f"📊 Content Size: {len(response.content)} bytes")
        print(f"📦 Content Type: {response.headers.get('content-type')}")
        
        # Save ZIP file in the project root with a clear name
        zip_filename = f"TEST_DOWNLOAD_{timestamp}.zip"
        zip_path = os.path.join(os.getcwd(), zip_filename)
        
        print(f"💾 Saving ZIP file to: {zip_path}")
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # Verify the file exists and has content
        if os.path.exists(zip_path):
            file_size = os.path.getsize(zip_path)
            print(f"✅ ZIP file saved successfully!")
            print(f"   📁 File: {zip_filename}")
            print(f"   📊 Size: {file_size} bytes")
            print(f"   📂 Location: {zip_path}")
            
            # Try to read ZIP contents
            try:
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    file_list = zip_ref.namelist()
                    print(f"   📋 ZIP Contents ({len(file_list)} files):")
                    for file_name in file_list:
                        file_info = zip_ref.getinfo(file_name)
                        print(f"     📄 {file_name} ({file_info.file_size} bytes)")
                    print("   ✅ ZIP file is valid and readable!")
            except Exception as zip_error:
                print(f"   ❌ ZIP validation error: {zip_error}")
            
            # Keep the file for inspection
            print(f"\n🎯 SUCCESS: ZIP file saved as '{zip_filename}' in project root!")
            print(f"   You can now see and inspect the ZIP file at: {zip_path}")
            
        else:
            print(f"❌ ZIP file was not saved properly")
    else:
        print(f"❌ Download failed: {response.text}")
    
    print("\n" + "=" * 40)
    print("📋 Test Summary:")
    print(f"   - User created and authenticated: ✅")
    print(f"   - Playbook created: ✅")
    print(f"   - Files uploaded: {uploaded_count} files")
    print(f"   - Download status: {response.status_code}")
    if response.status_code == 200:
        print(f"   - ZIP file created: ✅")
        print(f"   - ZIP file saved to project: ✅")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("🚀 ZIP File Creation Test")
    print("=" * 60)
    success = test_zip_creation()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Check the project root for the generated ZIP file.")
    else:
        print("\n❌ Test failed. Check the output above for details.")