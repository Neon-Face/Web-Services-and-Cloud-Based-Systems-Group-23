import re
import time
import threading
from flask import Flask, request, jsonify
import string
import base64

class SnowflakeIDGenerator:
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

        if self.machine_id > self.max_machine_id or self.machine_id < 0:
            raise ValueError(f"Machine ID must be between 0 and {self.max_machine_id}")

    def _current_timestamp(self):
        return int(time.time())

    def _wait_for_next_timestamp(self, last_timestamp):
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate_id(self):
        with self.lock:
            timestamp = self._current_timestamp()

            if timestamp < self.last_timestamp:
                raise Exception("Clock moved backwards. Refusing to generate ID.")

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    timestamp = self._wait_for_next_timestamp(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            id = (
                (timestamp << self.timestamp_shift) |
                (self.machine_id << self.machine_id_shift) |
                self.sequence
            )
            return id

# Base62
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase  # '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
def encode_base62(num):
    if num == 0:
        return BASE62_ALPHABET[0]
    
    base62 = []
    while num:
        num, rem = divmod(num, 62)
        base62.append(BASE62_ALPHABET[rem])
    
    return ''.join(reversed(base62))
     

URL_REGEX = re.compile(r'^(https?:\/\/)?([\w\.-]+)\.([a-z]{2,6})([\/\w .–#%()\[\]\'-]*)*\/?$', re.UNICODE)

app = Flask(__name__)
url_mapping = {}


id_generator = SnowflakeIDGenerator(machine_id=1) 

@app.route('/', methods=['POST'])
def create_short_url():
    data = request.get_json()
    url = data.get('value')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    short_id = str(encode_base62(id_generator.generate_id()))
    url_mapping[short_id] = url

    return jsonify({"id": short_id}), 201

@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id in url_mapping:
        return jsonify({"value": url_mapping[short_id]}), 301
    return jsonify({"error": "Not found"}), 404

@app.route('/<string:short_id>', methods=['PUT'])
def update_url(short_id):
    if short_id not in url_mapping:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json(force=True)

    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL'}), 400
    
    new_url = data['url']
    if not re.match(URL_REGEX, new_url):
        return jsonify({'error': 'Invalid URL'}), 400
    
    url_mapping[short_id] = new_url
    return jsonify({'message': 'Updated successfully'}), 200

@app.route('/<string:short_id>', methods=['DELETE'])
def delete_url(short_id):
    if short_id not in url_mapping:
        return jsonify({'error': 'Not found'}), 404
    del url_mapping[short_id]
    return '', 204

@app.route('/', methods=['GET'])
def list_urls():
    return jsonify({'urls': list(url_mapping.keys())}), 200

@app.route('/', methods=['DELETE'])
def delete_all():
    url_mapping.clear()
    return '', 404

if __name__ == '__main__':
    app.run(debug=True)