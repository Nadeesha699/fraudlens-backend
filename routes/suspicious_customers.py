from flask import Blueprint, jsonify
from database import get_db_connection

suspicious_bp = Blueprint("suspicious", __name__)


@suspicious_bp.route("", methods=["GET"])
def get_suspicious_customers():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                sc.id,
                sc.customer_id,
                sc.transaction_id,
                sc.customer_number,
                sc.suspicious_reason,
                sc.deposit_amount,
                sc.risk_level,
                sc.status,
                sc.updated_at,

                c.name,
                c.nic,
                c.email,
                c.phone

            FROM suspicious_customers sc

            LEFT JOIN customers c
                ON sc.customer_id = c.id

            ORDER BY sc.updated_at DESC
        """

        cursor.execute(query)
        customers = cursor.fetchall()

        return jsonify({
            "success": True,
            "customers": customers
        }), 200

    except Exception as e:

        print("Error loading suspicious customers:", e)

        return jsonify({
            "success": False,
            "error": "Failed to load suspicious customers"
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()