from flask import Blueprint, request, jsonify
import pandas as pd

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

@customers_bp.route("/<int:customer_id>/full-profile", methods=["GET"])
@token_required
def get_customer_full_profile(customer_id):

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(dictionary=True)

        # ==========================
        # CUSTOMER INFORMATION
        # ==========================

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
                "error": "Customer not found"
            }), 404


        # ==========================
        # SUSPICIOUS HISTORY
        # ==========================

        cursor.execute(
            """
            SELECT
                id,
                transaction_id,
                deposit_amount,
                suspicious_reason,
                risk_level,
                status,
                detected_at,
                updated_at
            FROM suspicious_customers
            WHERE customer_id = %s
            ORDER BY detected_at DESC
            """,
            (customer_id,)
        )

        suspicious_records = cursor.fetchall()


        # ==========================
        # TRANSACTION HISTORY
        # ==========================

        cursor.execute(
            """
            SELECT
                id,
                transaction_type,
                amount,
                transaction_date,
                created_at
            FROM transactions
            WHERE customer_id = %s
            ORDER BY transaction_date DESC
            """,
            (customer_id,)
        )

        transactions = cursor.fetchall()


        # ==========================
        # PROFILE SUMMARY
        # ==========================

        total_transactions = len(transactions)

        total_transaction_amount = sum(
            float(transaction["amount"] or 0)
            for transaction in transactions
        )

        suspicious_count = len(suspicious_records)


        return jsonify({

            "customer": customer,

            "summary": {
                "total_transactions": total_transactions,
                "total_transaction_amount": total_transaction_amount,
                "suspicious_count": suspicious_count
            },

            "suspicious_records": suspicious_records,

            "transactions": transactions

        }), 200


    except Exception as e:

        print("FULL PROFILE ERROR:", str(e))

        return jsonify({
            "error": "Failed to retrieve customer profile",
            "details": str(e)
        }), 500


    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()




@customers_bp.route("/upload", methods=["POST"])
def upload_excel():

    try:

        # Check file

        if "file" not in request.files:

            return jsonify({
                "error": "No file uploaded"
            }), 400


        file = request.files["file"]


        if file.filename == "":

            return jsonify({
                "error": "No file selected"
            }), 400


        # Read Excel

        df = pd.read_excel(
            file,
            engine="openpyxl"
        )


        # Required columns

        required_columns = [
            "Customer Number",
            "Name",
            "NIC",
            "Deposit Amount"
        ]


        for column in required_columns:

            if column not in df.columns:

                return jsonify({
                    "error":
                    f"Missing Excel column: {column}"
                }), 400


        conn = get_db_connection()

        cursor = conn.cursor(
            dictionary=True
        )


        results = []


        for _, row in df.iterrows():

            customer_number = str(
                row["Customer Number"]
            ).strip()


            nic = str(
                row["NIC"]
            ).strip()


            deposit_amount = float(
                row["Deposit Amount"]
            )


            # ==========================
            # FIND CUSTOMER
            # ==========================

            cursor.execute(
                """
                SELECT *
                FROM customers
                WHERE customer_number = %s
                OR nic = %s
                LIMIT 1
                """,
                (
                    customer_number,
                    nic
                )
            )


            customer = cursor.fetchone()


            # ==========================
            # CUSTOMER NOT FOUND
            # ==========================

            if not customer:

                results.append({

                    "customer_number":
                    customer_number,

                    "name":
                    row["Name"],

                    "deposit_amount":
                    deposit_amount,

                    "status":
                    "Customer Not Found"

                })

                continue


            # ==========================
            # SAVE TRANSACTION
            # ==========================

            cursor.execute(
                """
                INSERT INTO transactions (
                    customer_id,
                    transaction_type,
                    amount
                )

                VALUES (
                    %s,
                    'DEPOSIT',
                    %s
                )
                """,
                (
                    customer["id"],
                    deposit_amount
                )
            )


            transaction_id = cursor.lastrowid


            # ==========================
            # SUSPICIOUS CHECK
            # ==========================

            if deposit_amount > 100000:


                cursor.execute(
                    """
                    SELECT id
                    FROM suspicious_customers

                    WHERE customer_id = %s

                    AND deposit_amount = %s

                    LIMIT 1
                    """,
                    (
                        customer["id"],
                        deposit_amount
                    )
                )


                existing_suspicious = (
                    cursor.fetchone()
                )


                # Avoid duplicate suspicious record

                if not existing_suspicious:

                    cursor.execute(
                        """
                        INSERT INTO suspicious_customers (

                            customer_id,
                            transaction_id,
                            customer_number,
                            suspicious_reason,
                            deposit_amount,
                            risk_level,
                            status

                        )

                        VALUES (

                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            'HIGH',
                            'PENDING'

                        )
                        """,
                        (
                            (
    customer["id"],
    transaction_id,
    customer["customer_number"],
    "Deposit amount greater than 100,000",
    deposit_amount
)
                        )
                    )


                results.append({

                    "customer_number":
                    customer_number,

                    "name":
                    customer["name"],

                    "deposit_amount":
                    deposit_amount,

                    "status":
                    "SUSPICIOUS",

                    "risk_level":
                    "HIGH",

                    "reason":
                    "Deposit amount greater than 100,000"

                })


            else:

                results.append({

                    "customer_number":
                    customer_number,

                    "name":
                    customer["name"],

                    "deposit_amount":
                    deposit_amount,

                    "status":
                    "NORMAL",

                    "risk_level":
                    "LOW"

                })


        # Save database changes

        conn.commit()


        cursor.close()

        conn.close()


        return jsonify({

            "message":
            "Excel processed successfully",

            "results":
            results

        }), 200


    except Exception as e:

        return jsonify({

            "error":
            str(e)

        }), 500        