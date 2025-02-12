import re
import time
import threading
import unittest
import json
from flask import Flask, request, jsonify
import base62
from datetime import datetime
from base62_snowflake import app

class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        
        # Create test user and get authentication token
        user_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        # Create user (ignore if exists)
        self.app.post('/users', json=user_data)
        
        # Login to get token
        response = self.app.post('/users/login', json=user_data)
        self.assertEqual(response.status_code, 200, "Failed to login")
        
        self.auth_token = response.get_json()["token"]
        self.headers = {"Authorization": self.auth_token}

    def test_get_url_stats(self):
        print("\nTesting: Retrieving stats for a short URL")
        test_urls = [
            "https://en.wikipedia.org/wiki/Dijkstra's_algorithm",
            "https://en.wikipedia.org/wiki/Shortest_path_problem",
            "https://en.wikipedia.org/wiki/Bellman–Ford_algorithm",
            "https://en.wikipedia.org/wiki/Network_topology",
            "https://en.wikipedia.org/wiki/Physical_layer",
            "https://en.wikipedia.org/wiki/Bitstream"
        ]
        
        for url in test_urls:
            print(f"\nTesting URL: {url}")
            
            # Create shortened URL with auth
            response = self.app.post('/', 
                                   json={'value': url},
                                   headers=self.headers)
            self.assertEqual(response.status_code, 201, f"Failed to create shortened URL: {response.data}")
            
            data = response.get_json()
            short_id = data['id']
            print(f"Created short ID: {short_id}")
            
            # Test accessing URL (public endpoint)
            for _ in range(3):
                access_response = self.app.get(f'/{short_id}')
                self.assertEqual(access_response.status_code, 301, 
                               f"Failed to access URL: {access_response.data}")
            
            # Get stats with auth
            stats_response = self.app.get(f'/stats/{short_id}',
                                        headers=self.headers)
            self.assertEqual(stats_response.status_code, 200,
                           f"Failed to get stats: {stats_response.data}")
            
            stats_data = stats_response.get_json()
            
            # Format timestamps
            stats_data['created_at'] = datetime.fromtimestamp(
                stats_data['created_at']
            ).strftime('%Y-%m-%d %H:%M:%S')
            
            stats_data['last_accessed'] = datetime.fromtimestamp(
                stats_data['last_accessed']
            ).strftime('%Y-%m-%d %H:%M:%S') if stats_data['last_accessed'] else None
            
            print(f"Stats for {url}:", stats_data)
            
            # Verify stats
            self.assertEqual(stats_data['clicks'], 3,
                           f"Expected 3 clicks but got {stats_data['clicks']}")
            self.assertIsNotNone(stats_data['last_accessed'],
                               "Last accessed timestamp should not be None")
            self.assertIsNotNone(stats_data['created_at'],
                               "Created at timestamp should not be None")
            
        print("\nAll URL stats tests passed successfully")

    def test_auth_requirements(self):
        """Test authentication requirements"""
        print("\nTesting: Authentication requirements")
        test_url = "https://example.com"
        
        # Test without auth
        response = self.app.post('/', json={'value': test_url})
        self.assertEqual(response.status_code, 403,
                        "Should require authentication for POST")
        
        # Test with invalid auth
        response = self.app.post('/', 
                               json={'value': test_url},
                               headers={"Authorization": "invalid.token.here"})
        self.assertEqual(response.status_code, 403,
                        "Should reject invalid authentication")
        
        # Test with valid auth
        response = self.app.post('/',
                               json={'value': test_url},
                               headers=self.headers)
        self.assertEqual(response.status_code, 201,
                        "Should accept valid authentication")
        
        print("Authentication requirement tests passed successfully")
        
    def test_url_ownership(self):
        """Test URL ownership restrictions"""
        print("\nTesting: URL ownership restrictions")
        
        # Create a URL
        response = self.app.post('/',
                               json={'value': "https://example.com"},
                               headers=self.headers)
        self.assertEqual(response.status_code, 201)
        url_id = response.get_json()['id']
        
        # Create another user
        user2_data = {
            "username": "testuser2",
            "password": "testpass123"
        }
        self.app.post('/users', json=user2_data)
        
        # Login as second user
        response = self.app.post('/users/login', json=user2_data)
        self.assertEqual(response.status_code, 200)
        user2_token = response.get_json()["token"]
        user2_headers = {"Authorization": user2_token}
        
        # Try to modify first user's URL
        response = self.app.put(f'/{url_id}',
                              json={'url': "https://example.org"},
                              headers=user2_headers)
        self.assertEqual(response.status_code, 403,
                        "Should prevent other users from modifying URL")
                        
        print("URL ownership tests passed successfully")

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'headers'):
            self.app.delete('/', headers=self.headers)


if __name__ == '__main__':
    print("\n🚀 Starting URL Shortener Tests...")
    print("=====================================")
    unittest.main(verbosity=2)
