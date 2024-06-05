from flask import Flask
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def say_hello():
    return "Hello, world!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
