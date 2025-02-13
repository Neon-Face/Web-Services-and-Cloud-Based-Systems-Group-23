from flask import Flask,request,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import jwt
import database


app = Flask(__name__)


# Database (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
db_path = "instance/users.db"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
with app.app_context():
    db.create_all()

# 🌟
SECRET_KEY = "need_to_find_a_way_to_hind_this"

@app.route('/users',methods = ['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error':'Username and password are all required'}), 400
    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error':'Duplicate: Username already exists'}),409
    
    password_hash = generate_password_hash(password)
    new_user = User(username=username, password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message':'User registered successfully'}), 201

@app.route('/users', methods = ['PUT'])
def update_password():
    data = request.get_json()
    username = data.get('username')
    old_pwd = data.get('old-password')
    new_pwd = data.get('new-password')

    if not username or not old_pwd or not new_pwd:
        return jsonify({'error':'Username, old password and new password are all required'}),400
    
    user = User.query.filter_by(username=username).first()

    if user:
        if not check_password_hash(user.password_hash,old_pwd):
            print('Forbidden: Incorrect old password')
            return jsonify({'error':'Forbidden: Incorrect old password'}),403
        
        user.password_hash = generate_password_hash(new_pwd)
        db.session.commit()
        print('{}\'s password is updated successfully'.format(username))
        return jsonify({'message':'{}\'s password is updated successfully'.format(username)}),200
    else:
        print('User doesn\'t exist')
        return jsonify({'error':'User doesn\'t exist'}),400

@app.route('/users/login', methods = ['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error':'Username and password are all required', "token":"wrong"}),400
    
    user = User.query.filter_by(username=username).first()

    if user:
        if not check_password_hash(user.password_hash,password):
            print("Incorrect password")
            return jsonify({'error':'Forbidden: Incorrect password', "token":"wrong"}),403
        print('Token Generated')
        token = jwt.generate_jwt(username, SECRET_KEY)
        return jsonify({'token':token}),200
    else:
        print('User doesn\'t exist')
        return jsonify({'error':'User doesn\'t exist', "token":"wrong"}),400

if __name__ == '__main__':
    app.run(debug=True, port=8001)
