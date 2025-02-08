import re
import time
import threading
import unittest
from flask import Flask, request, jsonify
import base62
from datetime import datetime
from base64_snowflake import app


class URLShortenerTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

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
            response = self.app.post('/', json={'value': url})
            data = response.get_json()
            short_id = data['id']


            self.app.get(f'/{short_id}')
            self.app.get(f'/{short_id}')
            self.app.get(f'/{short_id}')

            stats_response = self.app.get(f'/stats/{short_id}')
            stats_data = stats_response.get_json()


            stats_data['created_at'] = datetime.fromtimestamp(stats_data['created_at']).strftime('%Y-%m-%d %H:%M:%S')
            stats_data['last_accessed'] = datetime.fromtimestamp(stats_data['last_accessed']).strftime(
                '%Y-%m-%d %H:%M:%S') if stats_data['last_accessed'] else None

            print(f"Stats for {url}:", stats_data)
            self.assertEqual(stats_response.status_code, 200)
            self.assertEqual(stats_data['clicks'], 3)
            self.assertIsNotNone(stats_data['last_accessed'])
            self.assertIsNotNone(stats_data['created_at'])


if __name__ == '__main__':
    unittest.main()
