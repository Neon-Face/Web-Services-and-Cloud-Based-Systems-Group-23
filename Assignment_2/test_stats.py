import re
import time
import threading
import unittest
import json
import requests
from flask import Flask, request, jsonify
import base62
from datetime import datetime
from authenticator import app as url_app

class URLShortenerTests(unittest.TestCase):
    auth_url = "http://127.0.0.1:8001"
    
    def setUp(self):
        self.app = url_app.test_client()
        self.app.testing = True
        
        # Get auth token from real auth service
        user_data = {
            "username": "luca",
            "password": "test_password"
        }
        
        try:
            # Create user (ignore if exists)
            requests.post(f"{self.auth_url}/users", json=user_data)
            
            # Login to get token
            response = requests.post(f"{self.auth_url}/users/login", json=user_data)
            if response.status_code != 200:
                raise Exception(f"Login failed: {response.text}")
                
            self.auth_token = response.json()["token"]
            self.headers = {"Authorization": self.auth_token}
            print("✓ Authentication setup complete")
            
        except Exception as e:
            print(f"⚠️  Auth setup failed: {str(e)}")
            self.skipTest("Authentication setup failed - is auth service running?")

    def test_get_url_stats(self):
        print("Testing: Retrieving stats for a short URL")
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
            self.assertEqual(response.status_code, 201, 
                          f"Failed to create shortened URL: {response.data}")
            
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

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'headers'):
            self.app.delete('/', headers=self.headers)
            print("✓ Cleanup complete")


if __name__ == '__main__':
    print("\n🚀 Starting URL Shortener Stats Tests...")
    print("=====================================")
    unittest.main(verbosity=2)
