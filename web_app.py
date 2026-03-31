from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pandas as pd
import joblib
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from fraud_predict import compute_features, predict_fraud, generate_otp
from email_utils import send_otp_email
from kafka_integration import get_kafka_producer

load_dotenv()

app = Flask(__name__)
CORS(app)
producer = get_kafka_producer()
KAFKA_TOPIC = 'fraud-transactions'

# -------------------------------
# In-memory customers (id 1-10)
# -------------------------------
CUSTOMERS = []
for i in range(1, 11):
    customer_id = f"C{i:09d}"
    CUSTOMERS.append({
        "customer_id": customer_id,
        "balance": 10000.0 + 1,
        "email": "kale.shrinath05@gmail.com",
        "phone": f"+100000000{i:02d}",
        "last_transaction": None,
        "password": "123",          # default password for non-fraud approve flow
        "verify_password": "456"   # required for two-step fraud completion
    })

COLLECTION_NAME = "customers"

# Pending fraud state keyed by sender_id
PENDING_FRAUD = {}


def get_customer_data(customer_id):
    """Fetch customer data from in-memory customer list."""
    return next((c for c in CUSTOMERS if c["customer_id"] == customer_id), None)

def update_customer_balance(customer_id, new_balance, last_transaction):
    """Update customer balance and last transaction in-memory."""
    for c in CUSTOMERS:
        if c["customer_id"] == customer_id:
            c["balance"] = new_balance
            c["last_transaction"] = last_transaction
            return c
    return None

def is_repeated_transaction(customer, sender_id, receiver_id, amount):
    last = customer.get("last_transaction")
    return last is not None and last.get("sender_id") == sender_id and last.get("receiver_id") == receiver_id and last.get("amount") == amount


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        sender_id = data.get('sender_id', '').strip()
        receiver_id = data.get('receiver_id', '').strip()
        amount = float(data.get('amount', 0))
        password = data.get('password', '').strip()

        if not sender_id or not receiver_id or amount <= 0:
            return jsonify({'error': 'Invalid input data'}), 400

        # Fetch customer data from in-memory list
        sender = get_customer_data(sender_id)
        receiver = get_customer_data(receiver_id)

        if sender is None or receiver is None:
            return jsonify({'error': 'Customer not found'}), 404

        # Block if sender has unresolved fraud pending
        if sender_id in PENDING_FRAUD and not PENDING_FRAUD[sender_id].get('verified', False):
            return jsonify({'error': 'Fraud verification pending. Payment operations disabled until second-step verification is complete.', 'pending_verification': True}), 403

        # Check balance
        if sender['balance'] < amount:
            return jsonify({'error': 'Insufficient balance'}), 400

        # Set balances
        oldbalanceOrg = sender['balance']
        newbalanceOrig = oldbalanceOrg - amount
        oldbalanceDest = receiver['balance']
        newbalanceDest = oldbalanceDest + amount

        # Repeat transaction flag
        repeat_txn = is_repeated_transaction(sender, sender_id, receiver_id, amount)

        # Compute features
        features_dict = compute_features(amount, oldbalanceOrg, newbalanceOrig,
                                       oldbalanceDest, newbalanceDest)

        # Load model
        if not os.path.exists("fraud_detection_model.pkl"):
            return jsonify({'error': 'Model not found'}), 500

        model = joblib.load("fraud_detection_model.pkl")

        # Predict
        prediction, probability, _ = predict_fraud(model, features_dict)

        # If repeat transaction was exact same as last time, force fraud
        if repeat_txn:
            prediction = 1
            probability = 1.0

        result = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'amount': amount,
            'oldbalanceOrg': oldbalanceOrg,
            'newbalanceOrig': newbalanceOrig,
            'oldbalanceDest': oldbalanceDest,
            'newbalanceDest': newbalanceDest,
            'errorBalanceOrig': features_dict['errorBalanceOrig'],
            'errorBalanceDest': features_dict['errorBalanceDest'],
            'prediction': prediction,
            'probability': probability,
            'status': 'normal' if prediction == 0 else 'fraud'
        }

        if prediction == 1:
            # Fraud suspected, require OTP email verification before final commit
            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            PENDING_FRAUD[sender_id] = {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'amount': amount,
                'verified': False,
                'otp': otp,
                'otp_expires_at': expires_at,
                'otp_attempts': 0
            }

            # Send OTP email in a best-effort manner
            try:
                send_otp_email(sender['email'], otp)
            except Exception as e:
                print(f"❌ OTP email send error: {e}")

            result['verification_required'] = True
            result['status'] = 'pending'
            result['message'] = f"Fraud suspected. OTP sent to {sender['email']}. Please verify to complete transaction."
        else:
            # For non-fraud we require the normal user password
            if password != sender.get('password'):
                return jsonify({'error': 'Invalid password for non-fraud transaction'}), 403

            result['message'] = 'Transaction approved.'

            # Update balances and last transactions in memory for both customers
            last_txn = {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'amount': amount
            }
            update_customer_balance(sender_id, newbalanceOrig, last_txn)
            update_customer_balance(receiver_id, newbalanceDest, last_txn)

        # Push event to Kafka for auditing and asynchronous processing
        kafka_payload = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'amount': amount,
            'prediction': prediction,
            'probability': probability,
            'status': result['status'],
            'timestamp': pd.Timestamp.now().isoformat()
        }

        try:
            producer.send(KAFKA_TOPIC, kafka_payload)
            producer.flush()
        except Exception as e:
            # Log the Kafka issue but keep API response unaffected
            print(f"🚨 Kafka publish error: {e}")
            result['kafka_error'] = str(e)

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        sender_id = data.get('sender_id', '').strip()
        otp_value = data.get('otp', '').strip()

        if not sender_id or not otp_value:
            return jsonify({'error': 'sender_id and otp are required'}), 400

        pending = PENDING_FRAUD.get(sender_id)

        if not pending:
            return jsonify({'verified': False, 'message': 'No pending fraud verification for this sender_id.'}), 404

        if pending.get('verified', False):
            return jsonify({'verified': True, 'message': 'Transaction already verified and processed.'}), 200

        # OTP expiration check
        if datetime.utcnow() > pending.get('otp_expires_at', datetime.utcnow()):
            del PENDING_FRAUD[sender_id]
            return jsonify({'verified': False, 'message': 'OTP expired. Transaction blocked.'}), 403

        if pending.get('otp_attempts', 0) >= 3:
            del PENDING_FRAUD[sender_id]
            return jsonify({'verified': False, 'message': 'Maximum OTP verification attempts exceeded. Transaction blocked.'}), 403

        if otp_value != pending.get('otp'):
            pending['otp_attempts'] = pending.get('otp_attempts', 0) + 1
            return jsonify({'verified': False, 'message': 'Invalid OTP. Please try again.'}), 403

        # second-step verified: complete pending transaction and clear lock
        receiver_id = pending['receiver_id']
        amount = pending['amount']

        sender = get_customer_data(sender_id)
        receiver = get_customer_data(receiver_id)

        if sender is None or receiver is None:
            return jsonify({'error': 'Customer not found during verification processing'}), 404

        if sender['balance'] < amount:
            # This should not happen if funds were previously checked in predict
            return jsonify({'verified': False, 'message': 'Insufficient balance to complete the pending transaction.'}), 400

        oldbalanceOrg = sender['balance']
        newbalanceOrig = oldbalanceOrg - amount
        oldbalanceDest = receiver['balance']
        newbalanceDest = oldbalanceDest + amount

        last_txn = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'amount': amount
        }

        update_customer_balance(sender_id, newbalanceOrig, last_txn)
        update_customer_balance(receiver_id, newbalanceDest, last_txn)

        pending['verified'] = True
        del PENDING_FRAUD[sender_id]

        return jsonify({
            'verified': True,
            'status': 'normal',
            'message': 'Successful transaction completed after OTP verification.',
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'amount': amount,
            'newbalanceOrig': newbalanceOrig,
            'newbalanceDest': newbalanceDest,
            'errorBalanceOrig': 0,
            'errorBalanceDest': 0,
            'probability': 0
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        return jsonify({"error": "Missing data"}), 400

    send_otp_email(email, otp)

    return jsonify({"message": "OTP sent successfully"})

if __name__ == '__main__':
    app.run(debug=True)