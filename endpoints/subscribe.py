from flask import Blueprint, request, jsonify
from services.email_service import send_email

subscribe_blueprint = Blueprint("subscribe", __name__)


@subscribe_blueprint.route("/<int:aircraft_id>/subscribe", methods=["POST"])
def subscribe_aircraft(aircraft_id):
    data = request.get_json()
    send_email(
        "Subscription Notice", "Subscription data received", "example@example.com"
    )
    return jsonify(
        {"status": "Subscription received for aircraft ID " + str(aircraft_id)}
    )
