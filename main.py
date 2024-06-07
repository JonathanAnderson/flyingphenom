import os
from flask import Flask, request, jsonify
from google.cloud import secretmanager
import gspread
from google.auth import default
import requests

app = Flask(__name__)

# Load secrets from Google Secret Manager
def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8")

# Set environment variables for secrets
os.environ['EMAIL'] = get_secret('AirSync_email')
os.environ['PASSWORD'] = get_secret('AirSync_password')
os.environ['FLIGHT_DATA'] = get_secret('AirSync_flight_data')

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

@app.route('/fetch_flights', methods=['GET'])
def fetch_flights():
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Failed to authenticate"}), 401

    url = "https://api.air-sync.com/api/v2/aircraft/"
    headers = {'Authorization': f'Bearer {auth_token}'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        aircraft = response.json()
        # Save aircraft data to Google Sheets
        for ac in aircraft:
            sheet.append_row([ac['id'], ac['tail_number'], ac['flight_time']])
        return jsonify({"message": "Data saved to Google Sheets"}), 200
    else:
        return jsonify({"error": "Failed to fetch flights"}), response.status_code

@app.route('/', methods=['GET'])
def say_hello():
    return "Hello, world!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
