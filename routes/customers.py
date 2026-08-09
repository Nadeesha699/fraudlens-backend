from flask import Blueprint, request, jsonify

from database import get_db_connection
from utils.security import token_required

customers_bp = Blueprint("customers", __name__)


@customers_bp.route("", methods=["POST"])
@token_required
def create_customer():

    data = request.get_json()

    customer_number = data.get("customer_number")
    name = data.get("name")
    nic = data.get("nic")
    phone = data.get("phone")
    email = data.get("email")
    address = data.get("address")

    if not customer_number or not name:
        return jsonify({
            "message": "Customer number and name are required"
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
            INSERT INTO customers
            (
                customer_number,
                name,
                nic,
                phone,
                email,
                address,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                customer_number,
                name,
                nic,
                phone,
                email,
                address,
                request.user["user_id"]
            )
        )

        connection.commit()

        return jsonify({
            "message": "Customer registered successfully"
        }), 201

    except Exception as error:

        connection.rollback()

        return jsonify({
            "message": str(error)
        }), 400

    finally:
        cursor.close()
        connection.close()


@customers_bp.route("", methods=["GET"])
@token_required
def get_customers():

    connection = get_db_connection()

    if not connection:
        return jsonify({
            "message": "Database connection failed"
        }), 500

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                c.id,
                c.customer_number,
                c.name,
                c.nic,
                c.phone,
                c.email,
                c.address,
                c.status,
                c.created_at,
                u.name AS created_by_name
            FROM customers c
            LEFT JOIN users u
                ON c.created_by = u.id
            ORDER BY c.created_at DESC
            """
        )

        customers = cursor.fetchall()

        return jsonify(customers), 200

    finally:
        cursor.close()
        connection.close()


@customers_bp.route("/<int:customer_id>", methods=["GET"])
@token_required
def get_customer(customer_id):

    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    try:

        cursor.execute(
            """
            SELECT
                id,
                customer_number,
                name,
                nic,
                phone,
                email,
                address,
                status,
                created_by,
                created_at,
                updated_at
            FROM customers
            WHERE id = %s
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:
            return jsonify({
                "message": "Customer not found"
            }), 404

        return jsonify(customer), 200

    finally:
        cursor.close()
        connection.close()