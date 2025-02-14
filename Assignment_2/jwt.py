import hmac
import hashlib
import base64
import json
import time
from flask import request

# Determin whether a user has permission
def has_permission(SECRET_KEY):
    token = request.headers.get('Authorization')
    if not token:
        print("Authorization token is required")
        return False
    if not verify_jwt(token,SECRET_KEY):
        print("No Permission: Invalid or expired token")
        return False
    # Get username
    _, payload, _ = parse_jwt(token)
    username = decode_base64_urlsafe(payload)['username']
    return username

def decode_base64_urlsafe(encoded_str):
    padding = "=" * (-len(encoded_str) % 4)
    encoded_str += padding
    decoded_bytes = base64.urlsafe_b64decode(encoded_str)
    return json.loads(decoded_bytes.decode())

# Generate JWT
def generate_header():
    header = {
        "alg":"HS256",
        "typ":"JWT"
    }
    return base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")

def generate_payload(username,expiration_hours=1):
    payload = {
        "username":username,
        "exp":int(time.time()) + expiration_hours * 3600
    }
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

def generate_signature(header,payload,secret_key):
    message = f"{header}.{payload}"
    signature = hmac.new(secret_key.encode(),message.encode() ,hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode().rstrip("=")

def generate_jwt(username, secret_key):
    header = generate_header()
    payload = generate_payload(username,1)
    signature = generate_signature(header,payload,secret_key)
    return f"{header}.{payload}.{signature}"

# Validate JWT
def parse_jwt(token):
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    return parts[0], parts[1], parts[2]

def verify_signature(header,payload,signature,secret_key):
    expected_signature = generate_signature(header,payload,secret_key)
    return hmac.compare_digest(expected_signature,signature)

def verify_expiration(payload):
    payload_data = json.loads(base64.urlsafe_b64decode(payload + "==").decode())
    expiration_time = payload_data.get("exp")
    if expiration_time is None or expiration_time < time.time():
        return False
    return True

def verify_jwt(token, secret_key):
    try:
        header, payload, signature = parse_jwt(token)
        if not verify_signature(header, payload, signature,secret_key):
            print("signature")
            return False
        if not verify_expiration(payload):
            print("expired")
            return False
        return True
    except Exception as e:
        print(f"JWT vertification failed: {e}")
        return False
    
