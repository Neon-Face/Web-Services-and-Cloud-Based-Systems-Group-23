from flask import Flask, request, jsonify
import hashlib
import hmac
import base64
import json
import time

auth_app = Flask(__name__)

users_db = {}

JWT_SECRET = "Web-Services-and-Cloud-Based-Systems-Group-23"

def generate_jwt(username):
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600  # 1 hour expiration
    }
    
    # Encode header and payload
    header = {"alg": "HS256", "typ": "JWT"}
    header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=')
    payload_encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=')
    
    # Create signature
    message = header_encoded + b'.' + payload_encoded
    signature = hmac.new(JWT_SECRET.encode(), message, hashlib.sha256)
    signature_encoded = base64.urlsafe_b64encode(signature.digest()).rstrip(b'=')
    
    # Combine all parts
    jwt = b'.'.join([header_encoded, payload_encoded, signature_encoded])
    return jwt.decode()

@auth_app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username in users_db:
        return jsonify({"error": "duplicate"}), 409
        
    # Hash password before storing
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    users_db[username] = {"password": password_hash}
    
    return '', 201

@auth_app.route('/users', methods=['PUT'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if username not in users_db:
        return jsonify({"error": "forbidden"}), 403
        
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    if users_db[username]["password"] != old_hash:
        return jsonify({"error": "forbidden"}), 403
        
    users_db[username]["password"] = hashlib.sha256(new_password.encode()).hexdigest()
    return '', 200

@auth_app.route('/users/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username not in users_db:
        return jsonify({"error": "forbidden"}), 403
        
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if users_db[username]["password"] != password_hash:
        return jsonify({"error": "forbidden"}), 403
        
    token = generate_jwt(username)
    return jsonify({"token": token}), 200

if __name__ == '__main__':
    auth_app.run(port=8001)
