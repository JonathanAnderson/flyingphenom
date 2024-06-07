from flask import Flask
from endpoints.logs import logs_blueprint
from endpoints.subscribe import subscribe_blueprint
from endpoints.debug import debug_blueprint

app = Flask(__name__)

# Register blueprints
app.register_blueprint(logs_blueprint)
app.register_blueprint(subscribe_blueprint)
app.register_blueprint(debug_blueprint)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
