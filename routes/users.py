from flask import Blueprint, jsonify, request

from database import get_db_connection
# from utils.security import token_required, manager_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/staff", methods=["GET"])
def get_staff():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                role,
                is_verified,
                is_active,
                created_at
            FROM users
            WHERE role = 'staff'
            ORDER BY created_at DESC
            """
        )

        staff = cursor.fetchall()

        return jsonify(staff), 200

    finally:
        cursor.close()
        connection.close()


@users_bp.route("/staff/<int:user_id>/verify", methods=["PUT"])
def verify_staff(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE users
            SET is_verified = TRUE
            WHERE id = %s
            AND role = 'staff'
            """,
            (user_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "message": "Staff member not found"
            }), 404

        return jsonify({
            "message": "Staff verified successfully"
        })

    finally:
        cursor.close()
        connection.close()


@users_bp.route("/staff/<int:user_id>", methods=["DELETE"])
def delete_staff(user_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM users
            WHERE id = %s
            AND role = 'staff'
            """,
            (user_id,)
        )

        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({
                "message": "Staff member not found"
            }), 404

        return jsonify({
            "message": "Staff deleted successfully"
        })

    finally:
        cursor.close()
        connection.close()