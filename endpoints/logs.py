from flask import Blueprint, jsonify
from services.secret_service import get_auth_token

logs_blueprint = Blueprint("logs", __name__)


@logs_blueprint.route("/<int:aircraft_id>/logs", methods=["GET"])
def get_logs(aircraft_id):
    auth_token = get_auth_token()
    # Implement the fetching logic
    return jsonify({"message": "Logs for aircraft " + str(aircraft_id)})
