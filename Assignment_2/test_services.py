import requests
import json

# test Authenticator
test_username = 'luca'
old_pwd = 'test_password'
new_pwd = ''

# test register
# response_create = requests.post('http://127.0.0.1:8001/users', json={'username': test_username, 'password': test_password})

# test update
# response_create = requests.put('http://127.0.0.1:8001/users', json={'username': test_username,'old-password': old_pwd , 'new-password': new_pwd})

# test login
response_login = requests.post('http://127.0.0.1:8001/users/login', json={'username': test_username,'password': old_pwd})
headers = {'Authorization': json.loads(response_login.content)["token"]}
# test Url_shortener
# test create url
response_1 = requests.post('http://127.0.0.1:8000/', headers=headers, json={'value': str("https://en.wikipedia.org/wiki/Docker_(software)")})


response_2 = requests.get('http://127.0.0.1:8000/', headers=headers)
print('🌟',response_2.json())

response_3 = requests.get('http://127.0.0.1:8000/VMF4a7E', headers=headers)
print('🌟',response_3.json())