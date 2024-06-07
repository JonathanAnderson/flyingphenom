import os
from flask import Flask, request, jsonify
from google.cloud import secretmanager
import gspread
from google.auth import default
import requests
from werkzeug.exceptions import HTTPException
import json

app = Flask(__name__)

# Define a cache dictionary to store data
data_cache = {}

# Load secrets from Google Secret Manager
def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8")

# Google Sheets authentication
credentials, project = default(scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
client = gspread.authorize(credentials)
sheet = client.open_by_key(os.getenv('FLIGHT_DATA')).sheet1

def get_auth_token():
    """Function to login and retrieve authentication token."""
    url = "https://api.air-sync.com/api/v2/user/login"
    payload = {
        'email': os.getenv('EMAIL'),
        'password': os.getenv('PASSWORD'),
        'grant_type': 'password'
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get('auth_token')
    else:
        return None

def fetch_and_cache_data(endpoint):
    """Fetch data from an endpoint and cache it."""
    if endpoint in data_cache:
        return data_cache[endpoint]  # Serve from cache if available

    auth_token = get_auth_token()
    if not auth_token:
        raise HTTPException(description="Failed to authenticate", code=401)

    headers = {'Authorization': f'Bearer {auth_token}'}
    response = requests.get(f"https://api.air-sync.com/api/v2/aircraft/{endpoint}/logs", headers=headers)
    if response.status_code == 200:
        data_cache[endpoint] = response.json()  # Cache the response
        return data_cache[endpoint]
    else:
        raise HTTPException(description="Failed to fetch data", code=response.status_code)

@app.route('/<int:aircraft_id>/logs', methods=['GET'])
def get_logs(aircraft_id):
    """Endpoint to get aircraft logs."""
    try:
        data = fetch_and_cache_data(aircraft_id)
        return jsonify(data)
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code

@app.route('/', methods=['GET'])
def say_hello():
    return "Hello, world!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
