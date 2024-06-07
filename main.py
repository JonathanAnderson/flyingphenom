import os
from flask import Flask, request, jsonify, render_template_string
from google.cloud import secretmanager
import gspread
from google.auth import default
import requests
from werkzeug.exceptions import HTTPException
from datetime import datetime
import json

app = Flask(__name__)

# Define a cache dictionary to store data
data_cache = {}
log_messages = []  # Store up to 100 log messages

# Google Sheets authentication
credentials, project = default(
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
)
client = gspread.authorize(credentials)
sheet = client.open_by_key(os.getenv("FLIGHT_DATA")).sheet1


def log_request(request_desc):
    global log_messages
    log_entry = {
        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'endpoint': request.path,
        'method': request.method,
        'data': request_desc
    }
    if len(log_messages) >= 100:
        log_messages.pop(0)
    log_messages.append(log_entry)


def get_auth_token():
    log_request('Attempting to get auth token')
    url = "https://api.air-sync.com/api/v2/user/login"
    payload = {
        "email": os.getenv("EMAIL"),
        "password": os.getenv("PASSWORD"),
        "grant_type": "password",
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("auth_token")
    else:
        return None


def fetch_and_cache_data(endpoint):
    log_request('Fetching data for endpoint: ' + str(endpoint))
    if endpoint in data_cache:
        return data_cache[endpoint]  # Serve from cache if available

    auth_token = get_auth_token()
    if not auth_token:
        raise HTTPException(description="Failed to authenticate", code=401)

    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        f"https://api.air-sync.com/api/v2/aircraft/{endpoint}/logs", headers=headers
    )
    if response.status_code == 200:
        data_cache[endpoint] = response.json()  # Cache the response
        return data_cache[endpoint]
    else:
        raise HTTPException(
            description="Failed to fetch data", code=response.status_code
        )


@app.route("/<int:aircraft_id>/logs", methods=["GET"])
def get_logs(aircraft_id):
    log_request('Requested logs for aircraft ID: ' + str(aircraft_id))
    try:
        data = fetch_and_cache_data(aircraft_id)
        return jsonify(data)
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code


@app.route("/<int:aircraft_id>/subscribe", methods=["POST"])
def subscribe_aircraft(aircraft_id):
    log_request('Received subscription for aircraft ID: ' + str(aircraft_id))
    data = request.json
    confirmation_url = data.get("SubscribeURL")
    if confirmation_url:
        # Simulate subscription confirmation by sending a GET request
        response = requests.get(confirmation_url)
        if response.status_code == 200:
            fetch_and_cache_data(str(aircraft_id))  # Refresh logs cache
            return jsonify({"status": "Subscription confirmed"}), 200
        else:
            return jsonify({"error": "Failed to confirm subscription"}), response.status_code
    return jsonify({"error": "No subscription URL provided"}), 400


@app.route("/debug", methods=["GET"])
def show_debug():
    log_request('Accessed debug logs')
    html = '''
    <table border="1">
        <tr>
            <th>Time</th><th>Endpoint</th><th>Method</th><th>Data</th>
        </tr>
        {% for log in logs %}
        <tr>
            <td>{{ log.time }}</td><td>{{ log.endpoint }}</td><td>{{ log.method }}</td><td>{{ log.data }}</td>
        </tr>
        {% endfor %}
    </table>
    '''
    return render_template_string(html, logs=log_messages)


@app.route("/", methods=["GET"])
def say_hello():
    log_request('Accessed root')
    return "Hello, world!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
