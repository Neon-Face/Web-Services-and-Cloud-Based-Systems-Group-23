import unittest
import requests
import json
import csv
import random


class TestApi(unittest.TestCase):
    # modify this to your local server settings
    base_url = "http://127.0.0.1:8000"
    auth_url = "http://127.0.0.1:8001"
    end_point = "/"
    test_username = "test"
    test_password = "test"
    create = "users"
    login = "users/login"

    url_create = f"{auth_url}{end_point}{create}"
    url_login = f"{auth_url}{end_point}{login}"
    
    def setUp(self):
        print("\n🔄 Setting up test environment...")
        
        # Reset headers before each test
        self.id_shortened_url_1 = ""
        self.id_shortened_url_2 = ""
        
        # Create user and get token
        try:
            # Create test user (ignore if exists)
            response_create = requests.post(self.url_create, 
                json={'username': self.test_username, 'password': self.test_password}
            )
            
            # Login to get token
            response_login = requests.post(self.url_login, 
                json={'username': self.test_username, 'password': self.test_password}
            )
            
            if response_login.status_code != 200:
                raise Exception(f"Login failed: {response_login.text}")
                
            self.headers = {'Authorization': json.loads(response_login.content)["token"]}
            self.headers_wrong = {'Authorization': 'wrong'}
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
                (self.url_to_shorten_1, self.url_to_shorten_2,
                 self.url_after_update, self.not_existing_id, self.invalid_url) = random.choice(data)
                print("✓ Test data loaded from CSV")
        except FileNotFoundError:
            print("⚠️  Using default test URLs")
            self.url_to_shorten_1 = "https://example.com"
            self.url_to_shorten_2 = "https://example.org"
            self.url_after_update = "https://example.net"
            self.not_existing_id = "nonexistent"
            self.invalid_url = "invalid://url"

        # Create initial test URLs
        def do_post(url_to_shorten):
            endpoint = "/"
            print(f"Creating URL: {url_to_shorten}")
            url = f"{self.base_url}{endpoint}"
            response = requests.post(url, headers=self.headers, json={'value': str(url_to_shorten)})
            self.assertEqual(response.status_code, 201, f"Expected status code 201, but got {response.status_code}")
            self.assertIsNotNone(response.text, "Response text should not be None.")
            response_extracted = response.json()
            id_returned = response_extracted["id"]
            return id_returned

        self.id_shortened_url_1 = do_post(self.url_to_shorten_1)
        print("id 1 obtained " + str(self.id_shortened_url_1))
        self.id_shortened_url_2 = do_post(self.url_to_shorten_2)
        print("id 2 obtained " + str(self.id_shortened_url_2))
        print("✓ Test environment setup complete\n")

    def tearDown(self):
        print("\n🧹 Cleaning up test environment...")
        if hasattr(self, 'headers'):
            endpoint = "/"
            url = f"{self.base_url}{endpoint}"
            response = requests.delete(url, headers=self.headers)
            self.assertEqual(response.status_code, 404, 
                f"Expected status code 404 to confirm correct erase, but got {response.status_code}")
        print("✓ Cleanup complete\n")

    def test_get_request_with_id_expect_301(self):
        id = self.id_shortened_url_1
        expected_value = self.url_to_shorten_1

        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.get(url, headers=self.headers)

        self.assertEqual(response.status_code, 301, 
            f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), expected_value,
            f"Expected response body to be {expected_value}, but got {response.json().get('value')}")

    def test_get_request_with_id_expect_404(self):
        id = "Unseen_id"
        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 404, 
            f"Expected status code 404, but got {response.status_code}")

    def test_put_id(self):
        id = self.id_shortened_url_1
        url_to_update = self.id_shortened_url_1
        url_after_update = self.url_after_update
        not_existing_id = self.not_existing_id
        invalid_url = self.invalid_url

        # Test with wrong auth
        endpoint = "/"
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.put(url, headers=self.headers_wrong, 
            data=json.dumps({'url': url_after_update}))
        self.assertEqual(response.status_code, 403, 
            f"Expected status code 403, but got {response.status_code}")

        # Test successful update
        url = f"{self.base_url}{endpoint}{id}"
        response = requests.put(url, headers=self.headers, 
            data=json.dumps({'url': url_after_update}))
        self.assertEqual(response.status_code, 200, 
            f"Expected status code 200, but got {response.status_code}")

        # Verify update
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.json().get("value"), url_after_update,
            f"Expected response body to be {url_after_update}, but got {response.json().get('value')}")

        # Test invalid URL
        response = requests.put(url, headers=self.headers, 
            data=json.dumps({'url': invalid_url}))
        self.assertEqual(response.status_code, 400, 
            f"Expected status code 400, but got {response.status_code}")

        # Test non-existent ID
        url = f"{self.base_url}{endpoint}{not_existing_id}"
        response = requests.put(url, headers=self.headers, 
            data=json.dumps({'url': not_existing_id}))
        self.assertEqual(response.status_code, 404, 
            f"Expected status code 404, but got {response.status_code}")

    def test_deletion_id(self):
        endpoint = "/"
        id = self.id_shortened_url_1
        url = f"{self.base_url}{endpoint}{id}"
        
        # Test wrong auth
        response = requests.delete(url, headers=self.headers_wrong)
        self.assertEqual(response.status_code, 403, 
            f"Expected status code 403, but got {response.status_code}")
        
        # Test successful deletion
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, 204, 
            f"Expected status code 204, but got {response.status_code}")
        
        # Verify deletion
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, 404, 
            f"Expected status code 404, but got {response.status_code}")

    def test_get_all(self):
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        
        # Test wrong auth
        response = requests.get(url, headers=self.headers_wrong)
        self.assertEqual(response.status_code, 403, 
            f"Expected status code 403, but got {response.status_code}")
        
        # Test successful get
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200, 
            f"Expected status code 200, but got {response.status_code}")
        self.assertIsNotNone(response.text, "Response text should not be None.")

    def test_post(self):
        url_to_shorten = "https://en.wikipedia.org/wiki/Docker_(software)"
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        
        # Test wrong auth
        response = requests.post(url, headers=self.headers_wrong, 
            json={'value': str(url_to_shorten)})
        self.assertEqual(response.status_code, 403, 
            f"Expected status code 403, but got {response.status_code}")
        
        # Test successful post
        response = requests.post(url, headers=self.headers, 
            json={'value': str(url_to_shorten)})
        self.assertEqual(response.status_code, 201, 
            f"Expected status code 201, but got {response.status_code}")
        self.assertIsNotNone(response.json().get("id"), "Response should contain an ID")
        
        # Verify created URL
        temp = response.json().get("id")
        url = f"{self.base_url}{endpoint}{temp}"
        response = requests.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 301, 
            f"Expected status code 301, but got {response.status_code}")
        self.assertEqual(response.json().get("value"), url_to_shorten,
            f"Expected response body to be {url_to_shorten}, but got {response.json().get('value')}")
        
        # Test empty URL
        url_to_shorten = ""
        url = f"{self.base_url}{endpoint}{url_to_shorten}"
        response = requests.post(url, headers=self.headers, 
            json={'value': str(url_to_shorten)})
        self.assertEqual(response.status_code, 400, 
            f"Expected status code 400, but got {response.status_code}")

    def test_deletion_all(self):
        endpoint = "/"
        url = f"{self.base_url}{endpoint}"
        
        # Test wrong auth
        response = requests.delete(url, headers=self.headers_wrong)
        self.assertEqual(response.status_code, 403,
            f"Expected status code 403, but got {response.status_code}")
        
        # Test successful deletion
        response = requests.delete(url, headers=self.headers)
        self.assertEqual(response.status_code, 404,
            f"Expected status code 404, but got {response.status_code}")
        
        # Verify deletion
        response = requests.get(url, headers=self.headers)
        self.assertIsNone(response.json().get("value"), 
            "The value should be None since should be empty.")


if __name__ == '__main__':
    unittest.main()
