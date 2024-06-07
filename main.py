import os
from flask import Flask, request, jsonify, render_template_string
from google.cloud import secretmanager
import gspread
from google.auth import default
import requests
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


def log_request(info):
    """Log request information, maintaining a maximum of 100 logs."""
    if len(log_messages) >= 100:
        log_messages.pop(0)
    log_messages.append(info)


def get_auth_token():
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


@app.route("/<int:aircraft_id>/logs", methods=["GET"])
def get_logs(aircraft_id):
    log_request("Requested logs for aircraft ID: " + str(aircraft_id))
    try:
        data = fetch_and_cache_data(aircraft_id)
        return jsonify(data)
    except HTTPException as e:
        return jsonify({"error": e.description}), e.code


@app.route("/<int:aircraft_id>/subscribe", methods=["POST"])
def subscribe_aircraft(aircraft_id):
    """Subscribe to notifications for a specific aircraft ID."""
    data = request.get_json()
    log_request(
        {
            "time": datetime.now().isoformat(),
            "action": "Received subscription",
            "aircraft_id": aircraft_id,
            "data": data,
        }
    )

    if "SubscribeURL" in data:
        confirmation_response = requests.get(data["SubscribeURL"])
        log_request(
            {
                "time": datetime.now().isoformat(),
                "action": "Subscription confirmation request",
                "aircraft_id": aircraft_id,
                "SubscribeURL": data["SubscribeURL"],
                "response_status": confirmation_response.status_code,
                "response_body": confirmation_response.text,
            }
        )
        return (
            jsonify(
                {
                    "status": "Subscription confirmed",
                    "response": confirmation_response.text,
                }
            ),
            confirmation_response.status_code,
        )

    return jsonify({"error": "SubscribeURL not provided"}), 400


@app.route("/debug", methods=["GET", "POST"])
def debug():
    """Display or log debug information."""
    if request.method == "POST":
        log_request(
            {
                "time": datetime.now().isoformat(),
                "action": "Debug POST",
                "data": request.get_json(),
            }
        )
        return jsonify({"status": "Debug data logged"}), 200
    else:
        log_request(
            {
                "time": datetime.now().isoformat(),
                "action": "Accessed debug logs",
            }
        )
        # Generate HTML table for display
        html = """
        <table border="1">
            <tr>
                <th>Time</th><th>Action</th><th>Details</th>
            </tr>
            {% for log in logs %}
            <tr>
                <td>{{ log.time }}</td>
                <td>{{ log.action }}</td>
                <td>{{ log.data }}</td>
            </tr>
            {% endfor %}
        </table>
        """
        return render_template_string(html, logs=log_messages)


@app.route("/", methods=["GET"])
def say_hello():
    log_request(
        {"time": datetime.now().isoformat(), "action": "Accessed root endpoint"}
    )
    return "Hello, world!"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
