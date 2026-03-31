import os
import pandas as pd
import joblib
import sys
import pymongo
import random
import string
from dotenv import load_dotenv

load_dotenv()

def connect_db():
    """Connect to MongoDB database."""
    try:
        mongo_uri = os.getenv("MMONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("DB_NAME", "fraud_db")
        client = pymongo.MongoClient(mongo_uri)
        db = client[db_name]
        return db
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

def get_customer_data(db, customer_id):
    """Fetch customer data from database."""
    customers = db["customers"]
    customer = customers.find_one({"customer_id": customer_id})
    if not customer:
        print(f"❌ Customer ID {customer_id} not found in database.")
        return None
    return customer

def generate_otp():
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def input_float(prompt):
    """Get valid float input from user."""
    while True:
        try:
            value = input(prompt).strip()
            return float(value)
        except ValueError:
            print("❌ Invalid input. Please enter a valid number (e.g., 123.45).")

def compute_features(amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest):
    """
    Calculate fraud detection features from raw input values.
    
    Features computed:
    - errorBalanceOrig: discrepancy in origin account
    - errorBalanceDest: discrepancy in destination account
    - errorBalanceOrig_1: binary flag (error exists in origin)
    - errorBalanceDest_1: binary flag (error exists in destination)
    """
    errorBalanceOrig = oldbalanceOrg - amount - newbalanceOrig
    errorBalanceDest = oldbalanceDest + amount - newbalanceDest
    
    return {
        "amount": amount,
        "oldbalanceOrg": oldbalanceOrg,
        "newbalanceOrig": newbalanceOrig,
        "oldbalanceDest": oldbalanceDest,
        "newbalanceDest": newbalanceDest,
        "errorBalanceOrig": errorBalanceOrig,
        "errorBalanceDest": errorBalanceDest,
        "errorBalanceOrig_1": int(errorBalanceOrig != 0),
        "errorBalanceDest_1": int(errorBalanceDest != 0),
    }

def predict_fraud(model, features_dict):
    """
    Run fraud detection model on transaction features.
    
    Returns:
    - prediction: 0 (normal) or 1 (fraud)
    - probability: fraud probability (0.0 to 1.0)
    """
    feature_names = [
        "amount", "oldbalanceOrg", "newbalanceOrig",
        "oldbalanceDest", "newbalanceDest",
        "errorBalanceOrig", "errorBalanceDest",
        "errorBalanceOrig_1", "errorBalanceDest_1"
    ]
    
    X = pd.DataFrame([features_dict], columns=feature_names)
    prediction = int(model.predict(X)[0])
    probability = float(model.predict_proba(X)[0][1])
    
    return prediction, probability, X

def display_result(sender_id, receiver_id, features_dict, prediction, probability):
    """Display fraud detection result in formatted output."""
    print("\n" + "="*60)
    print("FRAUD DETECTION RESULT")
    print("="*60)
    print(f"Sender ID          : {sender_id}")
    print(f"Receiver ID        : {receiver_id}")
    print(f"Transaction Amount : {features_dict['amount']:.2f}")
    print()
    print("Input Features:")
    print(f"  oldbalanceOrg    : {features_dict['oldbalanceOrg']:.2f}")
    print(f"  newbalanceOrig   : {features_dict['newbalanceOrig']:.2f}")
    print(f"  oldbalanceDest   : {features_dict['oldbalanceDest']:.2f}")
    print(f"  newbalanceDest   : {features_dict['newbalanceDest']:.2f}")
    print()
    print("Computed Features:")
    print(f"  errorBalanceOrig : {features_dict['errorBalanceOrig']:.2f}")
    print(f"  errorBalanceDest : {features_dict['errorBalanceDest']:.2f}")
    print(f"  errorBalanceOrig_1 : {features_dict['errorBalanceOrig_1']}")
    print(f"  errorBalanceDest_1 : {features_dict['errorBalanceDest_1']}")
    print()
    print("-"*60)
    print(f"Prediction         : {'FRAUD ⚠️' if prediction == 1 else 'NORMAL ✅'}")
    print(f"Fraud Probability  : {probability:.2%}")
    print("-"*60)
    
    if prediction == 1:
        print("🚨 RECOMMENDED ACTION: Block transaction and alert security team.")
    else:
        print("✅ RECOMMENDED ACTION: Transaction appears safe. Process normally.")
    print("="*60 + "\n")

def main(test_mode=False, test_sender="C123456789", test_receiver="C987654321", test_amount=5000.0):
    """Main program: collect user input and run fraud detection."""
    print("\n" + "="*60)
    print("FRAUD TRANSACTION DETECTION SYSTEM")
    print("="*60)
    print("Enter transaction details below:")
    print("="*60 + "\n")
    
    # Connect to database
    db = connect_db()
    
    # Get user input
    if test_mode:
        sender_id = test_sender
        receiver_id = test_receiver
        amount = test_amount
        print(f"Sender Customer ID   : {sender_id}")
        print(f"Receiver Customer ID : {receiver_id}")
        print(f"Transaction Amount   : {amount}")
    else:
        sender_id = input("Sender Customer ID   : ").strip()
        receiver_id = input("Receiver Customer ID : ").strip()
        amount = input_float("Transaction Amount   : ")
    
    # Fetch customer data
    sender = get_customer_data(db, sender_id)
    receiver = get_customer_data(db, receiver_id)
    
    if not sender or not receiver:
        print("❌ Transaction cannot proceed due to missing customer data.")
        return
    
    # Check if sender has sufficient balance
    if sender['balance'] < amount:
        print("❌ Insufficient balance in sender's account.")
        return
    
    # Set balances
    oldbalanceOrg = sender['balance']
    newbalanceOrig = oldbalanceOrg - amount
    oldbalanceDest = receiver['balance']
    newbalanceDest = oldbalanceDest + amount
    
    # Compute features
    features_dict = compute_features(amount, oldbalanceOrg, newbalanceOrig, 
                                      oldbalanceDest, newbalanceDest)
    
    # Load model
    try:
        model = joblib.load("fraud_detection_model.pkl")
    except FileNotFoundError:
        print("\n❌ ERROR: 'fraud_detection_model.pkl' not found.")
        print("   Please ensure the model file exists in the current directory.")
        print("   Run model.ipynb to generate and save the model first.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR loading model: {e}")
        sys.exit(1)
    
    # Predict
    try:
        prediction, probability, X = predict_fraud(model, features_dict)
    except Exception as e:
        print(f"\n❌ ERROR during prediction: {e}")
        sys.exit(1)
    
    # Display results
    display_result(sender_id, receiver_id, features_dict, prediction, probability)
    
    # Handle fraud detection
    if prediction == 1:
        print("\n🚨 FRAUD DETECTED! Sending OTP for verification...")
        otp = generate_otp()
        # For testing, print OTP instead of sending email
        if test_mode:
            print(f"TEST MODE: OTP is {otp}")
        else:
            send_otp_email(sender['email'], otp)
        
        # Ask for OTP verification
        if test_mode:
            entered_otp = otp  # Auto-verify in test mode
        else:
            entered_otp = input("Enter the OTP sent to your email: ").strip()
        if entered_otp == otp:
            print("✅ OTP verified. Transaction blocked due to fraud risk.")
        else:
            print("❌ Invalid OTP. Transaction blocked.")
    else:
        print("\n✅ Transaction approved. Processing...")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        main(test_mode=True)
    else:
        main()
