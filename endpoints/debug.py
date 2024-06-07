from flask import Blueprint, render_template_string

debug_blueprint = Blueprint("debug", __name__)


@debug_blueprint.route("/debug", methods=["GET"])
def show_debug():
    logs = []  # Fetch or calculate logs
    return render_template_string("<div>Debug Info</div>")
