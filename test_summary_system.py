#!/usr/bin/env python3
"""
Test script for the Summary System
Tests all endpoints to ensure they work correctly
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
SUMMARY_API = f"{BASE_URL}/api/summary"

# Test data
TEST_SESSION = "test-session-001"
TEST_USER = "test@example.com"
TEST_FILE = "GeM-Bidding-8255755.pdf"  # Adjust to your test file

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test health check endpoint."""
    print_header("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"✅ Health check passed")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_generate_summary():
    """Test summary generation."""
    print_header("Testing Summary Generation")
    try:
        payload = {
            "filename": TEST_FILE,
            "session_id": TEST_SESSION,
            "user_id": TEST_USER
        }
        print(f"Request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{SUMMARY_API}/generate", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary generated successfully")
            print(f"Summary length: {len(data.get('summary', ''))} characters")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_retrieve_summary():
    """Test summary retrieval."""
    print_header("Testing Summary Retrieval")
    try:
        response = requests.get(f"{SUMMARY_API}/retrieve/{TEST_FILE}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary retrieved successfully")
            print(f"Summary length: {len(data.get('summary', ''))} characters")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
            return True
        else:
            print(f"⚠️  Status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_list_summaries():
    """Test listing all summaries."""
    print_header("Testing List Summaries")
    try:
        response = requests.get(f"{SUMMARY_API}/list")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summaries listed successfully")
            print(f"Total summaries: {data.get('count', 0)}")
            for summary in data.get('summaries', [])[:5]:
                print(f"  - {summary.get('filename')}: {summary.get('length')} chars")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_condense_summary():
    """Test summary condensing."""
    print_header("Testing Summary Condensing")
    try:
        # First, get a summary to condense
        response = requests.get(f"{SUMMARY_API}/retrieve/{TEST_FILE}")
        
        if response.status_code != 200:
            print(f"⚠️  No saved summary to condense. Generate one first.")
            return False
        
        summary_text = response.json().get('summary', '')
        
        payload = {"summary_text": summary_text}
        response = requests.post(f"{SUMMARY_API}/condense", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summary condensed successfully")
            print(f"Original length: {len(summary_text)} characters")
            print(f"Condensed length: {len(data.get('condensed_summary', ''))} characters")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_combine_summaries():
    """Test combining multiple summaries."""
    print_header("Testing Combine Summaries")
    try:
        # For this test, we'll use the same file multiple times
        payload = {
            "filenames": [TEST_FILE],
            "session_id": TEST_SESSION,
            "user_id": TEST_USER
        }
        print(f"Request: {json.dumps(payload, indent=2)}")
        
        response = requests.post(f"{SUMMARY_API}/combine", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summaries combined successfully")
            print(f"Combined count: {data.get('combined_count', 0)}")
            print(f"Summary length: {len(data.get('summary', ''))} characters")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  SUMMARY SYSTEM TEST SUITE")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Test File: {TEST_FILE}")
    print(f"Session: {TEST_SESSION}")
    print(f"User: {TEST_USER}")
    
    results = {
        "Health Check": test_health_check(),
        "Generate Summary": test_generate_summary(),
        "Retrieve Summary": test_retrieve_summary(),
        "List Summaries": test_list_summaries(),
        "Condense Summary": test_condense_summary(),
        "Combine Summaries": test_combine_summaries(),
    }
    
    print_header("Test Results Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")

if __name__ == "__main__":
    main()
