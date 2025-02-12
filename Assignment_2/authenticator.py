from flask import Flask,request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

app = Flask(__name__)
SECRET_KEY = "need_to_find_a_way_to_hind_this"
user_db = {}

@app.route('/users',methods = ['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.getO('password')

    if not username or not password:
        return jsonify({'error':'Username and password are all required'}), 400
    
    if username in user_db:
        return jsonify({'duplicate':'Username already exists'}),409
    
    hashed_password = generate_password_hash(password)
    user_db[username] = {'password':hashed_password}

    return jsonify({'message':'User registered successfully'}), 201

@app.route('/users', methods = ['PUT'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    old_pwd = data.get('old-password')
    new_pwd = data.get('new-password')

    if not username or not old_pwd or not new_pwd:
        return jsonify({'error':'Username, old password and new password are all required'}),400
    
    if username not in user_db:
        return jsonify({'error':'User doesn\'t exist'}),400

    if not check_password_hash(user_db[username]['password'],old_pwd):
        return jsonify({'error':'Forbidden: Incorrect old password'}),403
    
    hashed_password = generate_password_hash(new_pwd)
    user_db[username]['password'] = hashed_password
    return jsonify({'message':'{}\'s password is updated successfully'.format(username)}),200

@app.route('/users/login', methods = ['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error':'Username and password are all required'})
    
    if username not in user_db:
        return jsonify({'error':'User doesn\'t exist'}),400

    if not check_password_hash(user_db[username]['password'], password):
        return jsonify({'error':'Forbidden: Incorrect password'}),403
    
    # generate jwt 
    token = jwt.generate_jwt(username, SECRET_KEY)
    return jsonify({'token':token}),200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
