from flask import Flask, request, jsonify, redirect
import re
import string
import random

app = Flask(__name__)

url_mapping = {}

def generate_short_id():
    return 

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

@app.route('/', methods=['GET'])
def get_keys():
    return jsonify(list(url_mapping.keys())), 200

@app.route('/', methods=['POST'])
def add_url():
    url = request.json.get('url')
    if not url or not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400
    
    short_id = generate_short_id()
    while short_id in url_mapping:
        short_id = generate_short_id()
    
    url_mapping[short_id] = url
    return jsonify({"id": short_id}), 201

@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id not in url_mapping:
        return jsonify({"error": "Not found"}), 404
    return redirect(url_mapping[short_id], code=301)

@app.route('/<short_id>', methods=['PUT'])
def update_url(short_id):
    if short_id not in url_mapping:
        return jsonify({"error": "Not found"}), 404
    
    url = request.json.get('url')
    if not url or not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400
    
    url_mapping[short_id] = url
    return jsonify({"id": short_id}), 200

@app.route('/<short_id>', methods=['DELETE'])
def delete_url(short_id):
    if short_id not in url_mapping:
        return jsonify({"error": "Not found"}), 404
    
    del url_mapping[short_id]
    return '', 204

@app.route('/', methods=['DELETE'])
def delete_all_urls():
    url_mapping.clear()
    return '', 404

if __name__ == '__main__':
    app.run(debug=True)