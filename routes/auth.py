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
    employee_id = data.get("employee_id")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    role = data.get("role")

    if not name or not email or not password or not phone or not employee_id:
        return jsonify({
            "error": "Name, email, phone number, employee_id and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    if role not in ["STAFF", "MANAGER"]:
        return jsonify({
            "error": "Invalid role"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "error": "Database connection failed"
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
                "error": "Email already registered"
            }), 409

        password_hash = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users
            (employee_id, name, email, phone, password_hash, role)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (employee_id, name, email, phone, password_hash, role)
        )

        connection.commit()

        return jsonify({
            "message": "Registration successful",
            "staff_id": employee_id
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500
     

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
            "error": "Email and password are required"
        }), 400

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "error": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                employee_id,
                name,
                email,
                password_hash,
                phone,
                role,
                status
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        # User not found
        if not user:
            return jsonify({
                "error": "Invalid email or password"
            }), 401

        # Password check
        if not verify_password(
            password,
            user["password_hash"]
        ):
            return jsonify({
                "error": "Invalid email or password"
            }), 401

        # Account pending
        if user["status"] == "PENDING":
            return jsonify({
                "error": "Your account is waiting for manager verification"
            }), 403

        # Account suspended
        if user["status"] == "SUSPENDED":
            return jsonify({
                "error": "Your account has been suspended"
            }), 403
        

        # Create JWT token
        token = create_token(
            user["id"],
            user["role"]
        )

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "employee_id": user["employee_id"],
                "name": user["name"],
                "email": user["email"],
                "phone": user["phone"],
                "role": user["role"],
                "status": user["status"]
            }
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        connection.close()