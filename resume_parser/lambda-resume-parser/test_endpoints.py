import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:3000"

def test_upload_endpoint():
    """Test the file upload endpoint"""
    print("\n=== Testing upload endpoint ===")
    
    # Create test file
    test_file = "test_resume.pdf"
    with open(test_file, "w") as f:
        f.write("This is a test file")
    
    try:
        with open(test_file, "rb") as f:
            files = {"file": (test_file, f, "application/pdf")}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            return response.json()["id"]
        return None
    except Exception as e:
        print(f"Upload error: {str(e)}")
        return None
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)

def test_status_endpoint(file_id):
    """Test the status endpoint"""
    print("\n=== Testing status endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/status/{file_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.json()
    except Exception as e:
        print(f"Error checking status: {str(e)}")
        return None

def test_list_resumes_endpoint():
    """Test the resume listing endpoint"""
    print("\n=== Testing listing endpoint ===")
    
    try:
        # List all resumes
        response = requests.get(f"{BASE_URL}/resumes")
        print("\nListing all resumes:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # List with limit
        response = requests.get(f"{BASE_URL}/resumes?limit=5")
        print("\nListing with limit of 5:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # List by status
        response = requests.get(f"{BASE_URL}/resumes?status=completed")
        print("\nListing completed resumes:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error listing resumes: {str(e)}")

def main():
    print("Starting endpoint tests...")
    
    # 1. Test file upload
    file_id = test_upload_endpoint()
    if not file_id:
        print("Error: Could not get file ID")
        return
    
    # 2. Wait and check status
    print("\nWaiting for processing...")
    for _ in range(10):  # Try 10 times
        status = test_status_endpoint(file_id)
        if status and status.get("status") in ["completed", "error"]:
            break
        time.sleep(2)
    
    # 3. Test resume listing
    test_list_resumes_endpoint()

if __name__ == "__main__":
    main() 