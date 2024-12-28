import requests

url = "http://127.0.0.1:5000/test"

files = {
    'file': open(r"D:\djsanghvi\notes\semester_5\ml2\ML 2 assignment 1.pdf", 'rb')  # Replace with the correct file path
}
data = {
    'user_id': 'user_1',
    'prompt':'Dont look into any other files'# Replace with your test user ID
}
response = requests.post(url, files=files, data=data)

print(response.status_code)
try:
    print(response.json())
except:
    print(response.text)