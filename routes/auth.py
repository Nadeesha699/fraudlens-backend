from flask import Blueprint, request, jsonify

from database import get_db_connection
from utils.security import (
    hash_password,
    verify_password,
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
        


        return jsonify({
            "message": "Login successful",
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

@auth_bp.route("/profile/<int:user_id>", methods=["GET"])
def get_user_profile(user_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                id,
                employee_id,
                name,
                email,
                phone,
                role,
                status,
                created_at,
                updated_at
            FROM users
            WHERE id = %s
        """

        cursor.execute(query, (user_id,))

        user = cursor.fetchone()

        if not user:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        return jsonify({
            "success": True,
            "user": user
        }), 200

    except Exception as e:

        print("Get user profile error:", e)

        return jsonify({
            "success": False,
            "error": "Failed to load user profile"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()  

@auth_bp.route("/profile/<int:user_id>", methods=["PUT"])
def update_user_profile(user_id):

    connection = None
    cursor = None

    try:

        data = request.get_json()

        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()

        # VALIDATION

        if not name:
            return jsonify({
                "success": False,
                "error": "Name is required"
            }), 400


        if not email:
            return jsonify({
                "success": False,
                "error": "Email is required"
            }), 400


        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # CHECK USER EXISTS

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        # CHECK EMAIL EXISTS

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = %s
            AND id != %s
            """,
            (
                email,
                user_id
            )
        )

        existing_email = cursor.fetchone()


        if existing_email:

            return jsonify({
                "success": False,
                "error": "Email is already in use"
            }), 400

        # UPDATE USER

        query = """
            UPDATE users
            SET
                name = %s,
                email = %s,
                phone = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """


        cursor.execute(
            query,
            (
                name,
                email,
                phone if phone else None,
                user_id
            )
        )


        connection.commit()

        # GET UPDATED USER

        cursor.execute(
            """
            SELECT
                id,
                employee_id,
                name,
                email,
                phone,
                role,
                status,
                created_at,
                updated_at
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )


        updated_user = cursor.fetchone()


        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": updated_user
        }), 200


    except Exception as e:

        print(
            "Update profile error:",
            e
        )


        if connection:
            connection.rollback()


        return jsonify({
            "success": False,
            "error": "Failed to update profile"
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@auth_bp.route(
    "/change-password/<int:user_id>",
    methods=["PUT"]
)
def change_password(user_id):

    connection = None
    cursor = None

    try:

        data = request.get_json()

        current_password = (
            data.get("current_password", "")
        )

        new_password = (
            data.get("new_password", "")
        )

        confirm_password = (
            data.get("confirm_password", "")
        )

        # VALIDATION

        if not current_password:
            return jsonify({
                "success": False,
                "error": "Current password is required"
            }), 400


        if not new_password:
            return jsonify({
                "success": False,
                "error": "New password is required"
            }), 400


        if not confirm_password:
            return jsonify({
                "success": False,
                "error": "Please confirm your new password"
            }), 400


        if new_password != confirm_password:
            return jsonify({
                "success": False,
                "error": "New passwords do not match"
            }), 400


        if len(new_password) < 8:
            return jsonify({
                "success": False,
                "error": "New password must be at least 8 characters"
            }), 400


        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # GET USER PASSWORD

        cursor.execute(
            """
            SELECT
                id,
                password_hash
            FROM users
            WHERE id = %s
            """,
            (user_id,)
        )


        user = cursor.fetchone()


        if not user:

            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404

        # CHECK CURRENT PASSWORD

        password_correct = (
            verify_password(
                current_password,
                user["password_hash"]
                
            )
        )


        if not password_correct:

            return jsonify({
                "success": False,
                "error": "Current password is incorrect"
            }), 400

        # CHECK SAME PASSWORD

        if current_password == new_password:

            return jsonify({
                "success": False,
                "error": "New password cannot be the same as your current password"
            }), 400

        # HASH NEW PASSWORD

        new_password_hash =  hash_password(new_password)

        # UPDATE PASSWORD

        cursor.execute(
            """
            UPDATE users
            SET
                password_hash = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (
                new_password_hash,
                user_id
            )
        )


        connection.commit()


        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200


    except Exception as e:

        print(
            "Change password error:",
            e
        )


        if connection:
            connection.rollback()


        return jsonify({
            "success": False,
            "error": "Failed to change password"
        }), 500


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()            
                  