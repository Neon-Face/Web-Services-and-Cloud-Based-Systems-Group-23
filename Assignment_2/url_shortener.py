import re
import time
import threading
from flask import Flask, request, jsonify
import base62
from authenticator import SECRET_KEY
import jwt


class Base62SnowflakeIDGenerator:
    def __init__(self, machine_id):
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

        self.timestamp_bits = 31
        self.machine_id_bits = 5
        self.sequence_bits = 5

        self.max_machine_id = (1 << self.machine_id_bits) - 1
        self.max_sequence = (1 << self.sequence_bits) - 1

        self.timestamp_shift = self.machine_id_bits + self.sequence_bits
        self.machine_id_shift = self.sequence_bits

    def current_timestamp(self):
        return int(time.time())

    def wait_for_next_timestamp(self, last_timestamp):
        timestamp = self.current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self.current_timestamp()
        return timestamp

    def generate_id(self):
        with self.lock:
            timestamp = self.current_timestamp()

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self.wait_for_next_timestamp(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id = (
                    (timestamp << self.timestamp_shift) |
                    (self.machine_id << self.machine_id_shift) |
                    self.sequence
            )

            id = base62.encode(id)
            return id


# Source: https://stackoverflow.com/a/17773849
URL_REGEX = re.compile(
    r'^(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'https?://(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9]+\.[^\s]{2,})$',
    re.UNICODE
)

app = Flask(__name__)

url_mapping = {}
stats_mapping = {}
id_generator = Base62SnowflakeIDGenerator(machine_id=1)

@app.route('/', methods=['POST'])
def create_short_url():

    username = jwt.has_permission(SECRET_KEY)
    if username:
        data = request.get_json()
        url = data.get('value')
        if not url:
            return jsonify({"error": "URL is required"}), 400
        if not re.match(URL_REGEX, url):
            return jsonify({'error': 'Invalid URL'}), 400

        short_id = str(id_generator.generate_id())
        timestamp = time.time()
        url_mapping[short_id] = {"url":url,'username':username}
        stats_mapping[short_id] = {"clicks": 0, "created_at": timestamp, "last_accessed": None,'username':username}
        return jsonify({"id": short_id}), 201
    
    else:
        return jsonify({"error": "Forbidden"}), 403


@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    
    username = jwt.has_permission(SECRET_KEY)

    if username:
        if not (short_id in url_mapping):
            return jsonify({"error": "Not found"}), 404
        # Can only redirect to his/her own url  
        if url_mapping[short_id]['username'] != username:
            return jsonify({"error": "Forbidden: You can only redirect to your own url"}), 403
        stats_mapping[short_id]["clicks"] += 1
        stats_mapping[short_id]["last_accessed"] = time.time()
        return jsonify({"value": url_mapping[short_id]['url']}), 301
    else:
        return jsonify({"error": "Forbidden: No permission"}), 403


@app.route('/<string:short_id>', methods=['PUT'])
def update_url(short_id):
    username = jwt.has_permission(SECRET_KEY)

    if username:
        if not (short_id in url_mapping):
            return jsonify({"error": "Not found"}), 404
        
        if url_mapping[short_id]['username'] != username:
            return jsonify({"error": "Forbidden: You can only update to your own url"}), 403

        data = request.get_json(force=True)

        if not data or 'url' not in data:
            return jsonify({'error': 'Missing URL'}), 400

        new_url = data['url']
        if not re.match(URL_REGEX, new_url):
            return jsonify({'error': 'Invalid URL'}), 400

        url_mapping[short_id]["url"] = new_url
        return jsonify({'value': 'Updated successfully'}), 200
    else:
        return jsonify({"error": "Forbidden: No permission"}), 403


@app.route('/<string:short_id>', methods=['DELETE'])
def delete_url(short_id):

    username = jwt.has_permission(SECRET_KEY)

    if username:
        if short_id not in url_mapping:
            return jsonify({'error': 'Not found'}), 404
        
        if url_mapping[short_id]['username'] != username:
            return jsonify({"error": "Forbidden: You can only delete to your own url"}), 403
        
        del url_mapping[short_id]
        del stats_mapping[short_id]
        return '', 204
    else:
        return jsonify({'error': 'Forbidden: No permission'}), 403


@app.route('/stats/<short_id>', methods=['GET'])
def get_url_stats(short_id):
    username = jwt.has_permission(SECRET_KEY)

    if username:
        if short_id not in url_mapping:
            return jsonify({"error": "Not found"}), 404
        
        if url_mapping[short_id]['username'] != username:
            return jsonify({"error": "Forbidden: You can only read your own url"}), 403
        
        return jsonify(url_mapping[short_id]), 200
    else:
        return jsonify({'error': 'Forbidden: No permission'}), 403


@app.route('/', methods=['GET'])
def list_urls():
    username = jwt.has_permission(SECRET_KEY)
    if username:
        filtered_urls = [entry['url'] for entry in url_mapping.values() if entry["username"] == username]
        return jsonify({'urls': filtered_urls}), 200
    else:
        return jsonify({'error': 'Forbidden: No permission'}), 403


@app.route('/', methods=['DELETE'])
def delete_user_urls():
    username = jwt.has_permission(SECRET_KEY)
    if username:
        urls_to_delete = [key for key, value in url_mapping.items() if value.get("username") == username]
        
        for key in urls_to_delete:
            url_mapping.pop(key, None)  
            stats_mapping.pop(key, None)  

        return '', 404  
    else:
        return jsonify({'error': 'Forbidden: No permission'}), 403


if __name__ == '__main__':
    app.run(debug=True, port=8000)
