from flask import Blueprint, request, jsonify

from database import get_db_connection
from utils.security import (
    hash_password,
    verify_password,
    create_token
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "staff")

    if not name or not email or not password:
        return jsonify({
            "message": "Name, email and password are required"
        }), 400

    if role not in ["staff", "manager"]:
        return jsonify({
            "message": "Invalid role"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return jsonify({
                "message": "Email already registered"
            }), 409

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            """,
            (name, email, password_hash, role)
        )

        connection.commit()

        return jsonify({
            "message": "Registration successful"
        }), 201

    finally:
        cursor.close()
        connection.close()


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "message": "Email and password are required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT id, name, email, password_hash,
                   role, is_verified, is_active
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        if not verify_password(
            password,
            user["password_hash"]
        ):
            return jsonify({
                "message": "Invalid email or password"
            }), 401

        if not user["is_active"]:
            return jsonify({
                "message": "Account is inactive"
            }), 403

        token = create_token(
            user["id"],
            user["role"]
        )

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "is_verified": bool(user["is_verified"])
            }
        })

    finally:
        cursor.close()
        connection.close()