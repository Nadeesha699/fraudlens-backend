from flask import Blueprint, jsonify
from database import get_db_connection

transactions_bp = Blueprint("transactions", __name__)


@transactions_bp.route("", methods=["GET"])
def get_all_transactions():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT
                t.id,
                t.customer_id,
                t.transaction_type,
                t.amount,
                t.transaction_date,
                t.created_at,

                c.customer_number,
                c.name,
                c.nic,
                c.email

            FROM transactions t

            LEFT JOIN customers c
                ON t.customer_id = c.id

            ORDER BY t.transaction_date DESC
        """

        cursor.execute(query)

        transactions = cursor.fetchall()

        return jsonify({
            "success": True,
            "transactions": transactions
        }), 200

    except Exception as e:

        print("Error loading transactions:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()