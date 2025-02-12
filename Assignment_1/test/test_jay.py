import unittest
import requests
import json
import csv
import random
import time


class TestApi(unittest.TestCase):
    base_url = "http://127.0.0.1:8000"
    auth_url = "http://127.0.0.1:8001"
    
    def get_auth_token(self):
        """Helper method to get authentication token"""
        # First create a test user if doesn't exist
        user_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        # Try to create user (ignore if already exists)
        requests.post(f"{self.auth_url}/users", json=user_data)
        
        # Login to get token
        response = requests.post(f"{self.auth_url}/users/login", json=user_data)
        if response.status_code == 200:
            return response.json()["token"]
        raise Exception("Failed to get auth token")

    def populate_variables_from_csv(self):
        print("\n📂 Loading test data from CSV file...")
        with open('read_from.csv', 'r') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            data = [row for row in reader if len(row) >= 5]
            random_row = random.choice(data)
            print(f"✓ Successfully loaded test data\n")
            return random_row

    def setUp(self):
        print("\n🔄 Setting up test environment...")
        # Get auth token first
        self.auth_token = self.get_auth_token()
        self.headers = {"Authorization": self.auth_token}
        
        self.id_shortened_url_1 = ""
        self.id_shortened_url_2 = ""

        # Load test URLs from CSV
        self.url_to_shorten_1, self.url_to_shorten_2, self.url_after_update, self.not_existing_id, self.invalid_url = self.populate_variables_from_csv()

        def do_post(url_to_shorten):
            endpoint = "/"
            print(f"📝 Creating shortened URL for: {url_to_shorten}")
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, json={'value': str(url_to_shorten)}, headers=self.headers)
            print(f"   Response Status: {response.status_code}")
            self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
            self.assertIsNotNone(response.text, "Response text should not be None.")
            response_extracted = response.json()
            id_returned = response_extracted["id"]
            print(f"   Generated ID: {id_returned}")
            return id_returned

        self.id_shortened_url_1 = do_post(self.url_to_shorten_1)
        self.id_shortened_url_2 = do_post(self.url_to_shorten_2)
        print("✓ Test environment setup complete\n")

    def tearDown(self):
        print("\n🧹 Cleaning up test environment...")
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        response = requests.delete(url, headers=self.headers)
        print("✓ Cleanup complete\n")

    def test_get_request_with_id_expect_301(self):
        print("\n🔍 Testing GET request with valid ID (expecting 301)...")
        id = self.id_shortened_url_1
        expected_value = self.url_to_shorten_1

        print(f"   Testing ID: {id}")
        print(f"   Expected URL: {expected_value}")

        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        # GET /:id is public, no auth needed
        response = requests.get(url)

        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")

        self.assertEqual(response.status_code, 301, f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), expected_value,
                         f"Expected URL: {expected_value}, but got {response.json().get('value')}")
        print("✓ Test passed\n")

    def test_get_request_with_id_expect_404(self):
        print("\n🔍 Testing GET request with invalid ID (expecting 404)...")
        id = "Unseen_id"
        print(f"   Testing with invalid ID: {id}")

        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.get(url)  # Public endpoint

        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_put_id(self):
        print("\n🔄 Testing PUT request to update URL...")
        id = self.id_shortened_url_1
        url_after_update = self.url_after_update
        not_existing_id = self.not_existing_id
        invalid_url = self.invalid_url

        # Test successful update
        print(f"   Testing successful update for ID: {id}")
        print(f"   New URL: {url_after_update}")
        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.put(url, data=json.dumps({'url': url_after_update}), headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")

        # Verify update
        print("   Verifying updated URL...")
        response = requests.get(url)  # Public endpoint
        self.assertEqual(response.json().get("value"), url_after_update,
                         f"Expected URL: {url_after_update}, but got {response.json().get('value')}")

        # Test invalid URL
        print(f"\n   Testing with invalid URL: {invalid_url}")
        response = requests.put(url, data=json.dumps({'url': invalid_url}), headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 400, f"Expected status code 400, but got {response.status_code}")

        # Test non-existent ID
        print(f"\n   Testing with non-existent ID: {not_existing_id}")
        url = f"{self.base_url}{endpoint}{not_existing_id}"
        response = requests.put(url, data=json.dumps({'url': url_after_update}), headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_deletion_id(self):
        print("\n❌ Testing URL deletion...")
        endpoint = "/"
        id = self.id_shortened_url_1
        print(f"   Attempting to delete ID: {id}")

        url = f"{self.base_url}{endpoint}{id}"
        response = requests.delete(url, headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 204, f"Expected status code 204, but got {response.status_code}")

        print("   Verifying deletion...")
        response = requests.delete(url, headers=self.headers)
        print(f"   Second deletion attempt status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_get_all(self):
        print("\n📋 Testing GET all URLs...")
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        self.assertIsNotNone(response.text, "Response text should not be None.")
        print("✓ Test passed\n")

    def test_post(self):
        print("\n📝 Testing POST request to create new URL...")
        url_to_shorten = "https://en.wikipedia.org/wiki/Docker_(software)"
        print(f"   URL to shorten: {url_to_shorten}")

        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json={'value': str(url_to_shorten)}, headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")

        self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
        self.assertIsNotNone(response.json().get("id"), "Response should contain an ID.")

        # Verify created URL
        print("   Verifying created URL...")
        temp = response.json().get("id")
        url = f"{self.base_url}{endpoint}{temp}"
        response = requests.get(url)  # Public endpoint
        print(f"   Verification Status: {response.status_code}")
        self.assertEqual(response.status_code, 301, f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), url_to_shorten,
                         f"Expected URL: {url_to_shorten}, but got {response.json().get('value')}")

        # Test empty URL
        print("\n   Testing with empty URL...")
        url_to_shorten = ""
        url = f"{self.base_url}{endpoint}{url_to_shorten}"
        response = requests.post(url, json={'value': str(url_to_shorten)}, headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 400, f"Expected status code 400, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_deletion_all(self):
        print("\n❌ Testing deletion of all URLs...")
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"

        print("   Deleting all URLs...")
        response = requests.delete(url, headers=self.headers)
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")

        print("   Verifying all URLs are deleted...")
        response = requests.get(url, headers=self.headers)
        print(f"   Verification Response: {response.text}")
        self.assertIsNotNone(response.text, "Response text should not be None.")
        print("✓ Test passed\n")

    def test_authentication(self):
        """Test authentication specific scenarios"""
        print("\n🔒 Testing authentication scenarios...")
        
        # Test without auth token
        print("   Testing request without auth token...")
        response = requests.post(f"{self.base_url}/", json={'value': 'https://example.com'})
        self.assertEqual(response.status_code, 403, "Expected 403 without auth token")
        
        # Test with invalid auth token
        print("   Testing request with invalid auth token...")
        response = requests.post(
            f"{self.base_url}/", 
            json={'value': 'https://example.com'},
            headers={"Authorization": "invalid_token"}
        )
        self.assertEqual(response.status_code, 403, "Expected 403 with invalid token")
        
        # Test with expired token (if implemented)
        print("   Testing request with expired token...")
        response = requests.post(
            f"{self.base_url}/", 
            json={'value': 'https://example.com'},
            headers={"Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MTYyMzkwMjIsInVzZXIiOiJ0ZXN0In0.invalid"}
        )
        self.assertEqual(response.status_code, 403, "Expected 403 with expired token")
        print("✓ Authentication tests passed\n")


if __name__ == '__main__':
    print("\n🚀 Starting URL Shortener API Tests...")
    print("=====================================")
    unittest.main(verbosity=2)
