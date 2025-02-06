from flask import Flask, request, jsonify
import re
import string
import random

app = Flask(__name__)
url_mapping = {}

def generate_short_id():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

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
def get_all_urls():
    return jsonify(list(url_mapping.keys())), 200

@app.route('/', methods=['POST'])
def create_short_url():
    data = request.get_json()
    url = data.get('value')
    if not url or not is_valid_url(url):
        return jsonify({"error": "Invalid URL"}), 400
    short_id = generate_short_id()
    url_mapping[short_id] = url
    return jsonify({"id": short_id}), 201

@app.route('/<short_id>', methods=['GET'])
def redirect_to_url(short_id):
    if short_id in url_mapping:
        return jsonify({"value": url_mapping[short_id]}), 301
    return jsonify({"error": "Not found"}), 404

@app.route('/<short_id>', methods=['PUT'])
def update_url(short_id):
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    new_url = data.get('url')
    if not new_url or not is_valid_url(new_url):
        return jsonify({"error": "Invalid URL"}), 400
    if short_id not in url_mapping:
        return jsonify({"error": "Not found"}), 404
    url_mapping[short_id] = new_url
    return jsonify({"message": "URL updated"}), 200

@app.route('/<short_id>', methods=['DELETE'])
def delete_url(short_id):
    if short_id in url_mapping:
        del url_mapping[short_id]
        return '', 204
    return jsonify({"error": "Not found"}), 404

@app.route('/', methods=['DELETE'])
def delete_all_urls():
    url_mapping.clear()
    return '', 404  # 返回404状态码表示未找到

if __name__ == '__main__':
    app.run(port=5000,debug=True)