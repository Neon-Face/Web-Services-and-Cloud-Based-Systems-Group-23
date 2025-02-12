import unittest
import requests
import json
import csv
import random
import time
from requests.exceptions import ConnectionError


class TestApi(unittest.TestCase):
    base_url = "http://127.0.0.1:8000"
    test_user = {"username": "testuser", "password": "testpass123"}
    
    @classmethod
    def setUpClass(cls):
        """Verify service is running before starting tests"""
        print("\n🔍 Checking if service is running...")
        try:
            requests.get(cls.base_url)
            print("✓ Service is running")
        except ConnectionError:
            raise unittest.SkipTest("Service is not running on port 8000")
    
    def setUp(self):
        """Set up test environment"""
        print("\n🔄 Setting up test environment...")
        
        # Create test user and get token
        try:
            # Create user (ignore if exists)
            requests.post(f"{self.base_url}/users", json=self.test_user)
            
            # Login to get token
            response = requests.post(f"{self.base_url}/users/login", json=self.test_user)
            if response.status_code != 200:
                raise Exception(f"Login failed: {response.text}")
                
            self.auth_token = response.json()["token"]
            self.headers = {"Authorization": self.auth_token}
            print("✓ Authentication setup complete")
            
        except Exception as e:
            print(f"⚠️  Auth setup failed: {str(e)}")
            self.skipTest("Authentication setup failed")

        # Load test URLs
        try:
            with open('read_from.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                data = [row for row in reader if len(row) >= 5]
                self.url_to_shorten_1, self.url_to_shorten_2, self.url_after_update, self.not_existing_id, self.invalid_url = random.choice(data)
                print("✓ Test data loaded from CSV")
        except FileNotFoundError:
            print("⚠️  Using default test URLs")
            self.url_to_shorten_1 = "https://example.com"
            self.url_to_shorten_2 = "https://example.org"
            self.url_after_update = "https://example.net"
            self.not_existing_id = "nonexistent"
            self.invalid_url = "invalid://url"

        # Create initial test URLs
        self.id_shortened_url_1 = self.create_url(self.url_to_shorten_1)
        self.id_shortened_url_2 = self.create_url(self.url_to_shorten_2)
        
        if not self.id_shortened_url_1 or not self.id_shortened_url_2:
            self.skipTest("Failed to create test URLs")
            
        print("✓ Test environment setup complete\n")

    def create_url(self, url):
        """Helper method to create a shortened URL"""
        try:
            response = requests.post(
                f"{self.base_url}/", 
                json={'value': url}, 
                headers=self.headers
            )
            if response.status_code == 201:
                return response.json()["id"]
        except Exception as e:
            print(f"⚠️  Failed to create URL: {str(e)}")
        return None

    def tearDown(self):
        """Clean up after tests"""
        print("\n🧹 Cleaning up test environment...")
        if hasattr(self, 'headers'):
            try:
                requests.delete(f"{self.base_url}/", headers=self.headers)
                print("✓ Cleanup complete")
            except Exception as e:
                print(f"⚠️  Cleanup failed: {str(e)}")
        print("")

    def test_authentication(self):
        """Test authentication scenarios"""
        print("\n🔒 Testing authentication scenarios...")
        
        # Test without auth token
        print("   Testing request without auth token...")
        response = requests.post(
            f"{self.base_url}/", 
            json={'value': 'https://example.com'}
        )
        self.assertEqual(response.status_code, 403, "Expected 403 without auth token")
        
        # Test with invalid auth token
        print("   Testing request with invalid auth token...")
        response = requests.post(
            f"{self.base_url}/", 
            json={'value': 'https://example.com'},
            headers={"Authorization": "invalid.token.here"}
        )
        self.assertEqual(response.status_code, 403, "Expected 403 with invalid token")
        
        # Test with expired token
        print("   Testing request with expired token...")
        response = requests.post(
            f"{self.base_url}/", 
            json={'value': 'https://example.com'},
            headers={"Authorization": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MTYyMzkwMjJ9.invalid"}
        )
        self.assertEqual(response.status_code, 403, "Expected 403 with expired token")
        print("✓ Authentication tests passed\n")

    def test_get_request_with_id_expect_301(self):
        """Test getting a URL with valid ID"""
        if not self.id_shortened_url_1:
            self.skipTest("Failed to create test URL")
            
        print("\n🔍 Testing GET request with valid ID...")
        print(f"   Testing ID: {self.id_shortened_url_1}")
        print(f"   Expected URL: {self.url_to_shorten_1}")
        
        response = requests.get(f"{self.base_url}/{self.id_shortened_url_1}")
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        
        self.assertEqual(response.status_code, 301, f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), self.url_to_shorten_1,
                      f"Expected URL: {self.url_to_shorten_1}, but got {response.json().get('value')}")
        print("✓ Test passed\n")

    def test_get_request_with_id_expect_404(self):
        """Test getting a URL with invalid ID"""
        print("\n🔍 Testing GET request with invalid ID...")
        print(f"   Testing with invalid ID: {self.not_existing_id}")
        
        response = requests.get(f"{self.base_url}/{self.not_existing_id}")
        print(f"   Response Status: {response.status_code}")
        
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_put_id(self):
        """Test updating a URL"""
        if not self.id_shortened_url_1:
            self.skipTest("Failed to create test URL")
            
        print("\n✏️ Testing PUT request...")
        
        # Test successful update
        print(f"   Testing successful update for ID: {self.id_shortened_url_1}")
        print(f"   New URL: {self.url_after_update}")
        
        response = requests.put(
            f"{self.base_url}/{self.id_shortened_url_1}",
            data=json.dumps({'url': self.url_after_update}),
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        
        # Verify update
        response = requests.get(f"{self.base_url}/{self.id_shortened_url_1}")
        self.assertEqual(response.json().get("value"), self.url_after_update,
                      f"Expected URL: {self.url_after_update}, but got {response.json().get('value')}")
        
        # Test invalid URL
        print(f"\n   Testing with invalid URL: {self.invalid_url}")
        response = requests.put(
            f"{self.base_url}/{self.id_shortened_url_1}",
            data=json.dumps({'url': self.invalid_url}),
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 400, f"Expected status code 400, but got {response.status_code}")
        
        # Test non-existent ID
        print(f"\n   Testing with non-existent ID: {self.not_existing_id}")
        response = requests.put(
            f"{self.base_url}/{self.not_existing_id}",
            data=json.dumps({'url': self.url_after_update}),
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_deletion_id(self):
        """Test deleting a specific URL"""
        if not self.id_shortened_url_1:
            self.skipTest("Failed to create test URL")
            
        print("\n❌ Testing DELETE request...")
        print(f"   Attempting to delete ID: {self.id_shortened_url_1}")
        
        response = requests.delete(
            f"{self.base_url}/{self.id_shortened_url_1}",
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 204, f"Expected status code 204, but got {response.status_code}")
        
        # Verify deletion
        print("   Verifying deletion...")
        response = requests.get(f"{self.base_url}/{self.id_shortened_url_1}")
        print(f"   Verification Status: {response.status_code}")
        self.assertEqual(response.status_code, 404, f"Expected status code 404, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_get_all(self):
        """Test getting all URLs"""
        print("\n📋 Testing GET all URLs...")
        response = requests.get(
            f"{self.base_url}/",
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        
        self.assertEqual(response.status_code, 200, f"Expected status code 200, but got {response.status_code}")
        self.assertIsNotNone(response.json().get("urls"), "Response should contain 'urls' key")
        print("✓ Test passed\n")

    def test_post(self):
        """Test creating a new shortened URL"""
        print("\n📝 Testing POST request...")
        url_to_shorten = "https://example.com/test"
        print(f"   URL to shorten: {url_to_shorten}")
        
        # Create URL
        response = requests.post(
            f"{self.base_url}/",
            json={'value': url_to_shorten},
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        print(f"   Response Body: {response.text}")
        
        self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
        self.assertIsNotNone(response.json().get("id"), "Response should contain 'id' key")
        
        # Verify creation
        id = response.json()["id"]
        response = requests.get(f"{self.base_url}/{id}")
        print(f"   Verification Status: {response.status_code}")
        self.assertEqual(response.status_code, 301, f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), url_to_shorten,
                      f"Expected URL: {url_to_shorten}, but got {response.json().get('value')}")
        
        # Test empty URL
        print("\n   Testing with empty URL...")
        response = requests.post(
            f"{self.base_url}/",
            json={'value': ""},
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 400, f"Expected status code 400, but got {response.status_code}")
        print("✓ Test passed\n")

    def test_deletion_all(self):
        """Test deleting all URLs"""
        print("\n❌ Testing deletion of all URLs...")
        
        # Delete all URLs
        response = requests.delete(
            f"{self.base_url}/",
            headers=self.headers
        )
        print(f"   Response Status: {response.status_code}")
        self.assertEqual(response.status_code, 204, f"Expected status code 204, but got {response.status_code}")
        
        # Verify deletion
        print("   Verifying all URLs are deleted...")
        response = requests.get(
            f"{self.base_url}/",
            headers=self.headers
        )
        print(f"   Verification Response: {response.text}")
        self.assertEqual(len(response.json()["urls"]), 0, "All URLs should be deleted")
        print("✓ Test passed\n")


if __name__ == '__main__':
    print("\n🚀 Starting URL Shortener API Tests...")
    print("=====================================")
    unittest.main(verbosity=2)
