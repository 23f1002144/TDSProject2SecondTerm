#!/usr/bin/env python3
"""
Simple test script for the Data Analyst Agent API
"""

import requests
import json
import sys


def test_api_endpoint(url="http://localhost:8000"):
    """Test the basic API functionality"""

    print(f"🧪 Testing API at: {url}")
    print("=" * 60)

    # Test 1: Health check
    print("\n1️⃣ Testing Health Endpoint...")
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return

    # Test 2: Simple question (no data files)
    print("\n2️⃣ Testing Simple Question...")
    try:
        with open("test_simple.txt", "w") as f:
            f.write("Answer with a JSON array: [What is 5 + 3?]")

        with open("test_simple.txt", "rb") as f:
            files = {"files": ("test_simple.txt", f, "text/plain")}
            response = requests.post(f"{url}/api/", files=files, timeout=60)

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Result: {result}")
        else:
            print(f"   ❌ Error: {response.text}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Data analysis
    print("\n3️⃣ Testing Data Analysis...")
    try:
        files = [
            (
                "files",
                ("test_analysis.txt", open("test_analysis.txt", "rb"), "text/plain"),
            ),
            (
                "files",
                (
                    "sample_movies.csv",
                    open("examples/sample_movies.csv", "rb"),
                    "text/csv",
                ),
            ),
        ]

        response = requests.post(f"{url}/api/", files=files, timeout=120)

        # Close files
        for file_tuple in files:
            file_tuple[1][1].close()

        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Analysis completed!")
            if isinstance(result, list):
                for i, item in enumerate(result):
                    if isinstance(item, str) and item.startswith("data:image"):
                        print(f"   [{i}]: <base64 image data>")
                    else:
                        print(f"   [{i}]: {item}")
            else:
                print(f"   Result: {result}")
        else:
            print(f"   ❌ Error: {response.text}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 60)
    print("🎉 Testing completed!")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_api_endpoint(url)
