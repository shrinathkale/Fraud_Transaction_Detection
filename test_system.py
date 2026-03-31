"""
Test script to verify the fraud detection system is working correctly.
Run this to test both single and batch prediction modes.
"""

import sys
import os
import pandas as pd
import joblib

def test_model_exists():
    """Check if the model file exists."""
    print("✓ Test 1: Checking model file...")
    if os.path.exists("fraud_detection_model.pkl"):
        print("  ✅ fraud_detection_model.pkl found")
        return True
    else:
        print("  ❌ fraud_detection_model.pkl NOT found")
        print("     ACTION: Run model.ipynb to train and save the model")
        return False

def test_model_loads():
    """Check if the model can be loaded."""
    print("\n✓ Test 2: Loading model...")
    try:
        model = joblib.load("fraud_detection_model.pkl")
        print("  ✅ Model loaded successfully")
        return True, model
    except Exception as e:
        print(f"  ❌ Failed to load model: {e}")
        return False, None

def test_single_prediction(model):
    """Test single transaction prediction."""
    print("\n✓ Test 3: Single transaction prediction...")
    try:
        # Import prediction function
        from fraud_predict import compute_features, predict_fraud
        
        # Test data
        features = compute_features(
            amount=500.0,
            oldbalanceOrg=1000.0,
            newbalanceOrig=500.0,
            oldbalanceDest=2000.0,
            newbalanceDest=2500.0
        )
        
        # Predict
        prediction, probability, _ = predict_fraud(model, features)
        
        print(f"  ✅ Prediction successful")
        print(f"     Amount: $500.00")
        print(f"     Result: {'FRAUD' if prediction == 1 else 'NORMAL'}")
        print(f"     Confidence: {probability:.2%}")
        return True
    except Exception as e:
        print(f"  ❌ Prediction failed: {e}")
        return False

def test_batch_input_file():
    """Check if example input file exists."""
    print("\n✓ Test 4: Checking batch input file...")
    if os.path.exists("example_transactions.csv"):
        df = pd.read_csv("example_transactions.csv")
        print(f"  ✅ example_transactions.csv found ({len(df)} transactions)")
        return True
    else:
        print("  ❌ example_transactions.csv NOT found")
        return False

def test_batch_prediction(model):
    """Test batch prediction mode."""
    print("\n✓ Test 5: Batch predictions...")
    try:
        from fraud_predict import compute_features, predict_fraud
        
        df = pd.read_csv("example_transactions.csv")
        
        feature_names = [
            "amount", "oldbalanceOrg", "newbalanceOrig",
            "oldbalanceDest", "newbalanceDest",
            "errorBalanceOrig", "errorBalanceDest",
            "errorBalanceOrig_1", "errorBalanceDest_1"
        ]
        
        predictions = []
        for _, row in df.head(3).iterrows():  # Test first 3 rows
            features = compute_features(
                row['amount'], row['oldbalanceOrg'], row['newbalanceOrig'],
                row['oldbalanceDest'], row['newbalanceDest']
            )
            X = pd.DataFrame([features], columns=feature_names)
            pred = int(model.predict(X)[0])
            prob = float(model.predict_proba(X)[0][1])
            predictions.append((pred, prob))
        
        print(f"  ✅ Batch prediction successful ({len(predictions)} transactions)")
        for i, (pred, prob) in enumerate(predictions):
            print(f"     Transaction {i+1}: {'FRAUD' if pred == 1 else 'NORMAL'} ({prob:.2%})")
        return True
    except Exception as e:
        print(f"  ❌ Batch prediction failed: {e}")
        return False

def test_required_files():
    """Check if all required project files exist."""
    print("\n✓ Test 6: Checking required files...")
    required_files = [
        "fraud.csv",
        "model.ipynb",
        "fraud_predict.py",
        "fraud_predict_batch.py",
        "requirements.txt",
        "README.md",
        "QUICKSTART.md"
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"  ⚠️  Missing files: {', '.join(missing)}")
        return False
    else:
        print(f"  ✅ All required files present")
        return True

def main():
    """Run all tests."""
    print("="*60)
    print("FRAUD DETECTION SYSTEM - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Model file exists
    results.append(("Model file exists", test_model_exists()))
    
    if not results[-1][1]:
        print("\n❌ CRITICAL: Model not found. Cannot proceed with other tests.")
        print("    Run: jupyter notebook model.ipynb")
        return
    
    # Test 2: Model loads
    model_ok, model = test_model_loads()
    results.append(("Model loads", model_ok))
    
    if not model_ok:
        print("\n❌ CRITICAL: Failed to load model.")
        return
    
    # Test 3: Single prediction works
    results.append(("Single prediction", test_single_prediction(model)))
    
    # Test 4: Batch input file exists
    results.append(("Batch input file", test_batch_input_file()))
    
    # Test 5: Batch prediction works
    results.append(("Batch prediction", test_batch_prediction(model)))
    
    # Test 6: Required files
    results.append(("Required files", test_required_files()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {test_name}")
    
    print("="*60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("  1. Run: python fraud_predict.py")
        print("  2. Or:  python fraud_predict_batch.py example_transactions.csv")
        print("  3. Or:  python fraud_predict_batch.py your_data.csv")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
    
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
