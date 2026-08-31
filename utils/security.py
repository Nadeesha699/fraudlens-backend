from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from config import Config


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)


# def create_token(user_id, role):
#     payload = {
#         "user_id": user_id,
#         "role": role
#     }

#     return jwt.encode(
#         payload,
#         Config.JWT_SECRET,
#         algorithm="HS256"
#     )


# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):

#         token = request.headers.get("Authorization")

#         if not token:
#             return jsonify({
#                 "message": "Authorization token required"
#             }), 401

#         try:
#             token = token.replace("Bearer ", "")

#             payload = jwt.decode(
#                 token,
#                 Config.JWT_SECRET,
#                 algorithms=["HS256"]
#             )

#             request.user = payload

#         except jwt.InvalidTokenError:
#             return jsonify({
#                 "message": "Invalid or expired token"
#             }), 401

#         return f(*args, **kwargs)

#     return decorated


# def manager_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):

#         if request.user["role"] != "manager":
#             return jsonify({
#                 "message": "Manager access required"
#             }), 403

#         return f(*args, **kwargs)

#     return decorated