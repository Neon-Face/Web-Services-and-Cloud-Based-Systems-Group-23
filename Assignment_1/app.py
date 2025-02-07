import json
from flask import Flask, request, jsonify, redirect
import re
import random
import string

app = Flask(__name__)

url_mapping = {}

BASE62 = string.ascii_letters + string.digits

URL_REGEX = re.compile(r'^(https?:\/\/)?([\w\.-]+)\.([a-z]{2,6})([\/\w .–#%()\[\]\'-]*)*\/?$', re.UNICODE)

def generate_short_id(length=6):
    while True:
        short_id = ''.join(random.choices(BASE62, k=length))
        if short_id not in url_mapping:
            return short_id

@app.route('/', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if not data:
        print('not data Missing URL')
        return jsonify({'error': 'Missing URL'}), 400
    
    original_url = data['value']

    if not original_url:
        print('not original_url Missing URL')
        return jsonify({'error': 'Missing URL'}), 400

    if not re.match(URL_REGEX, original_url):
        print('Invalid URL',original_url)
        return jsonify({'error': 'Invalid URL'}), 400
    
    short_id = generate_short_id()
    url_mapping[short_id] = original_url
    return jsonify({'id': short_id}), 201


@app.route('/<string:short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id in url_mapping:
        return jsonify({"value": url_mapping[short_id]}), 301
    return jsonify({'error': 'Not found'}), 404

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
    if short_id in url_mapping:
        del url_mapping[short_id]
        return '', 204
    return jsonify({'error': 'Not found'}), 404

@app.route('/', methods=['GET'])
def list_urls():
    return jsonify({'urls': list(url_mapping.keys())}), 200

@app.route('/', methods=['DELETE'])
def delete_all():
    url_mapping.clear()
    return '', 404

if __name__ == '__main__':
    app.run(debug=True)
