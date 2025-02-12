import re
import time
import threading
import hmac
import hashlib
import base64
import json
from functools import wraps
from flask import Flask, request, jsonify
import base62

JWT_SECRET = "Web-Services-and-Cloud-Based-Systems-Group-23" 

def verify_jwt(token):
    try:
        # Split the JWT into its parts
        header_b64, payload_b64, signature_b64 = token.split('.')
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}".encode()
        expected_signature = base64.urlsafe_b64decode(signature_b64 + '=' * (-len(signature_b64) % 4))
        actual_signature = hmac.new(JWT_SECRET.encode(), message, hashlib.sha256).digest()
        
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None
            
        # Decode payload
        payload_str = base64.urlsafe_b64decode(payload_b64 + '=' * (-len(payload_b64) % 4))
        payload = json.loads(payload_str)
        
        # Check expiration
        if payload.get('exp', 0) < time.time():
            return None
            
        return payload.get('sub')  # Return username
    except:
        return None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "forbidden"}), 403
            
        username = verify_jwt(auth_header)
        if not username:
            return jsonify({"error": "forbidden"}), 403
            
        request.user = username
        return f(*args, **kwargs)
    return decorated

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

# Modified to store user ownership
url_mapping = {}
stats_mapping = {}

id_generator = Base62SnowflakeIDGenerator(machine_id=1)

@app.route('/', methods=['POST'])
@require_auth
def create_short_url():
    data = request.get_json()
    url = data.get('value')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    short_id = str(id_generator.generate_id())
    timestamp = time.time()
    
    url_mapping[short_id] = {
        "url": url,
        "user": request.user
    }
    stats_mapping[short_id] = {
        "clicks": 0,
        "created_at": timestamp,
        "last_accessed": None
    }

    return jsonify({"id": short_id}), 201

@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id in url_mapping:
        stats_mapping[short_id]["clicks"] += 1
        stats_mapping[short_id]["last_accessed"] = time.time()
        return jsonify({"value": url_mapping[short_id]["url"]}), 301
    return jsonify({"error": "Not found"}), 404

@app.route('/<string:short_id>', methods=['PUT'])
@require_auth
def update_url(short_id):
    if short_id not in url_mapping:
        return jsonify({'error': 'Not found'}), 404
        
    if url_mapping[short_id]["user"] != request.user:
        return jsonify({'error': 'forbidden'}), 403

    data = request.get_json(force=True)
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400

    new_url = data['url']
    if not re.match(URL_REGEX, new_url):
        return jsonify({'error': 'Invalid URL'}), 400

    url_mapping[short_id]["url"] = new_url
    return jsonify({'message': 'Updated successfully'}), 200

@app.route('/<string:short_id>', methods=['DELETE'])
@require_auth
def delete_url(short_id):
    if short_id not in url_mapping:
        return jsonify({'error': 'Not found'}), 404
        
    if url_mapping[short_id]["user"] != request.user:
        return jsonify({'error': 'forbidden'}), 403
        
    del url_mapping[short_id]
    del stats_mapping[short_id]
    return '', 204

@app.route('/stats/<short_id>', methods=['GET'])
@require_auth
def get_url_stats(short_id):
    if short_id not in stats_mapping:
        return jsonify({"error": "Not found"}), 404
        
    if url_mapping[short_id]["user"] != request.user:
        return jsonify({'error': 'forbidden'}), 403
        
    return jsonify(stats_mapping[short_id]), 200

@app.route('/', methods=['GET'])
@require_auth
def list_urls():
    # Only return URLs owned by the requesting user
    user_urls = {
        id: data["url"]
        for id, data in url_mapping.items()
        if data["user"] == request.user
    }
    return jsonify({'urls': list(user_urls.keys())}), 200

@app.route('/', methods=['DELETE'])
@require_auth
def delete_all():
    # Only delete URLs owned by the requesting user
    ids_to_delete = [
        id for id, data in url_mapping.items()
        if data["user"] == request.user
    ]
    
    for id in ids_to_delete:
        del url_mapping[id]
        del stats_mapping[id]
        
    return '', 204

if __name__ == '__main__':
    app.run(debug=True, port=8000)
