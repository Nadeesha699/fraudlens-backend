from flask import Flask
from flask_cors import CORS

from routes.auth import auth_bp
from routes.users import users_bp
from routes.customers import customers_bp
from routes.suspicious_customers import suspicious_bp


app = Flask(__name__)

CORS(app)


app.register_blueprint(
    auth_bp,
    url_prefix="/api/auth"
)

app.register_blueprint(
    users_bp,
    url_prefix="/api/users"
)

app.register_blueprint(
    customers_bp,
    url_prefix="/api/customers"
)


app.register_blueprint(
    suspicious_bp,
    url_prefix="/api"
)


@app.route("/")
def home():
    return {
        "message": "FraudLens API is running"
    }


@app.route("/api/health")
def health():
    return {
        "status": "ok"
    }


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )