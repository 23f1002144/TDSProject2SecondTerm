#!/usr/bin/env python3

import requests
import json
import os


def test_api(base_url="http://localhost:8000"):
    """Test the data analyst API with sample questions."""

    # Test 1: Wikipedia scraping example
    print("Testing Wikipedia scraping...")

    questions1 = """Scrape the list of highest grossing films from Wikipedia. It is at the URL:
https://en.wikipedia.org/wiki/List_of_highest-grossing_films

Answer the following questions and respond with a JSON array of strings containing the answer.

1. How many $2 bn movies were released before 2000?
2. Which is the earliest film that grossed over $1.5 bn?
3. What's the correlation between the Rank and Peak?
4. Draw a scatterplot of Rank and Peak along with a dotted red regression line through it.
   Return as a base-64 encoded data URI, `"data:image/png;base64,iVBORw0KG..."` under 100,000 bytes."""

    # Create temp file for questions
    with open("test_questions1.txt", "w") as f:
        f.write(questions1)

    try:
        # Send request
        files = {
            "files": ("questions.txt", open("test_questions1.txt", "rb"), "text/plain")
        }

        response = requests.post(f"{base_url}/api/", files=files, timeout=180)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")

        if response.status_code == 200:
            result = response.json()
            print(f"Result type: {type(result)}")
            if isinstance(result, list):
                print(f"Array with {len(result)} elements")
                for i, item in enumerate(result):
                    print(f"  [{i}]: {str(item)[:100]}...")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        if os.path.exists("test_questions1.txt"):
            os.remove("test_questions1.txt")

    print("\n" + "=" * 50 + "\n")

    # Test 2: Simple data analysis
    print("Testing simple analysis...")

    questions2 = """Analyze the provided data and answer:
1. What is the average value?
2. What is the correlation between column A and B?"""

    # Create sample CSV data
    sample_data = """A,B,C
1,2,3
4,5,6
7,8,9
10,11,12"""

    with open("test_questions2.txt", "w") as f:
        f.write(questions2)

    with open("test_data.csv", "w") as f:
        f.write(sample_data)

    try:
        files = [
            (
                "files",
                ("questions.txt", open("test_questions2.txt", "rb"), "text/plain"),
            ),
            ("files", ("data.csv", open("test_data.csv", "rb"), "text/csv")),
        ]

        response = requests.post(f"{base_url}/api/", files=files, timeout=60)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        # Clean up
        for file in ["test_questions2.txt", "test_data.csv"]:
            if os.path.exists(file):
                os.remove(file)


def test_health(base_url="http://localhost:8000"):
    """Test the health endpoint."""
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"Testing API at: {base_url}")
    print("=" * 50)

    test_health(base_url)
    print()
    test_api(base_url)
