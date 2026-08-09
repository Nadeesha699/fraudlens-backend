# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import pandas as pd
# from database import get_connection

# app = Flask(__name__)
# CORS(app)

# @app.route("/upload", methods=["POST"])
# def upload_excel():

#     try:
#         # check file exists
#         if "file" not in request.files:
#             return jsonify({"error": "No file uploaded"}), 400

#         file = request.files["file"]

#         # read excel (IMPORTANT FIX: specify engine)
#         df = pd.read_excel(file, engine="openpyxl")

#         conn = get_connection()
#         cursor = conn.cursor(dictionary=True)

#         results = []

#         for _, row in df.iterrows():

#             customer_id = int(row["ID"])

#             cursor.execute(
#                 "SELECT * FROM customers WHERE id=%s",
#                 (customer_id,)
#             )

#             customer = cursor.fetchone()

#             results.append({
#                 "uploaded": {
#                     "id": row["ID"],
#                     "name": row["Name"],
#                     "age": row["Age"],
#                     "email": row["Email"]
#                 },
#                 "status": "Found" if customer else "Not Found",
#                 "database": customer
#             })

#         cursor.close()
#         conn.close()

#         return jsonify(results), 200

#     except Exception as e:
#         return jsonify({
#             "error": str(e)
#         }), 500


# if __name__ == "__main__":
#     app.run(debug=True)

from flask import Flask
from flask_cors import CORS

from routes.auth import auth_bp
from routes.users import users_bp
from routes.customers import customers_bp


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