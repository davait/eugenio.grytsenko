#! /usr/bin/env python

import requests
import json
import time

def test_resume_upload():
    # API endpoint
    base_url = "http://localhost:3000"
    
    # Test file path - replace with your test resume file
    file_path = "test_resume.pdf"
    
    print("1. Uploading resume file...")
    # Upload file
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/pdf')}
        response = requests.post(f"{base_url}/upload", files=files)
    
    if response.status_code != 201:
        print(f"Error uploading file: {response.text}")
        return
    
    file_id = response.json()['id']
    print(f"File uploaded successfully. ID: {file_id}")
    
    # Wait for processing
    print("\n2. Waiting for processing...")
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        status_response = requests.get(f"{base_url}/status/{file_id}")
        status_data = status_response.json()
        
        print(f"Current status: {status_data['status']}")
        
        if status_data['status'] == 'completed':
            print("\n3. Processing completed!")
            print("AI Response:")
            print(json.dumps(status_data['ai_response'], indent=2))
            break
        elif status_data['status'] == 'error':
            print("\nError processing file!")
            break
            
        time.sleep(2)
        attempt += 1
    
    # List all resumes
    print("\n4. Listing all resumes...")
    list_response = requests.get(f"{base_url}/resumes")
    print(f"Total resumes: {len(list_response.json())}")
    print("\nAll resumes:")
    print(json.dumps(list_response.json(), indent=2))

if __name__ == "__main__":
    test_resume_upload()
