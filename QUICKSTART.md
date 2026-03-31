# QUICK START GUIDE

## 1. Install dependencies
```bash
pip install -r requirements.txt
```

## 2. Setup Database
Ensure MongoDB is running, then setup sample data:
```bash
python setup_db.py
```

## 3. Train the Model (First Time Only)
Open and run `model.ipynb`:
```bash
jupyter notebook model.ipynb
```

This will create `fraud_detection_model.pkl`

## 4. Run Fraud Detection

### Option A: Web Interface (Recommended)

```bash
python web_app.py
```

Open `http://localhost:5000` in your browser for an attractive web interface with:
- Modern gradient design
- Real-time fraud analysis
- OTP verification system
- Responsive mobile layout
- Detailed transaction results

**Sample Data for Testing:**
- Sender ID: `C123456789`
- Receiver ID: `C987654321`
- Amount: `1000.00`
- Easy form input
- Visual fraud analysis results
- OTP verification system
- Responsive design

### Option B: Command Line Interface

```bash
python fraud_predict.py
```

Then enter your transaction details when prompted:
```
Sender Customer ID   : C123456789
Receiver Customer ID : C987654321
Transaction Amount   : 1000.00
```

The system will:
- Fetch balances from MongoDB
- Calculate fraud features
- Predict fraud probability
- Send OTP if fraud detected
- Output success/failure status

Output:
```
FRAUD DETECTION RESULT
============================================================
Sender ID          : C123456789
Receiver ID        : C987654321
Prediction         : NORMAL ✅
Fraud Probability  : 0.00%
============================================================

✅ Transaction approved. Processing...
```

### Option B: Test Mode
```bash
python fraud_predict.py test
```

Runs with sample data for testing.

### Option C: Batch (Multiple Transactions from CSV)
```bash
python fraud_predict_batch.py example_transactions.csv fraud_predictions.csv
```

**Input CSV format:**
```
customer_id,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest
CUST001,181.0,181.0,0.0,21182.0,21363.0
CUST002,329.0,329.0,0.0,21145.0,21474.0
```

**Output CSV:**
```
customer_id,amount,prediction,fraud_probability,errorBalanceOrig,errorBalanceDest
CUST001,181.0,0,0.0123,0.0,0.0
CUST002,329.0,0,0.0234,0.0,0.0
```

---

## File Descriptions

| File | Purpose |
|------|---------|
| `model.ipynb` | Train the fraud detection model (run once) |
| `fraud.csv` | Raw training dataset |
| `fraud_detection_model.pkl` | Saved trained model (auto-generated) |
| `fraud_predict.py` | Predict fraud for single transaction (interactive) |
| `fraud_predict_batch.py` | Predict fraud for multiple transactions (batch CSV) |
| `example_transactions.csv` | Sample transactions for testing batch mode |
| `requirements.txt` | Python package dependencies |
| `README.md` | Full documentation |

---

## Input Features Explained

When entering transaction data, you need:

- **Customer ID**: Unique identifier (e.g., "CUST001")
- **Amount**: Transaction amount in currency (e.g., 500.00)
- **Old Balance Origin**: Sender's balance BEFORE transaction (e.g., 1000.00)
- **New Balance Origin**: Sender's balance AFTER transaction (e.g., 500.00)
- **Old Balance Dest**: Receiver's balance BEFORE transaction (e.g., 2000.00)
- **New Balance Dest**: Receiver's balance AFTER transaction (e.g., 2500.00)

### Example: $500 Transfer

```
Sender account:
  Before: $1000 (old balance)
  Transfer: $500
  After: $500 (new balance)

Receiver account:
  Before: $2000 (old balance)
  Receive: $500
  After: $2500 (new balance)
```

---

## Understanding Results

### Prediction

- **0 = NORMAL** ✅ (Low fraud risk)
- **1 = FRAUD** ⚠️ (High fraud risk)

### Fraud Probability

- **0% - 20%**: Very likely normal
- **20% - 40%**: Probably normal
- **40% - 60%**: Uncertain (review manually)
- **60% - 80%**: Probably fraudulent
- **80% - 100%**: Very likely fraudulent

### Error Balances

- `errorBalanceOrig = 0`: Origin account math is correct
- `errorBalanceDest = 0`: Destination account math is correct
- Non-zero values indicate discrepancies (potential fraud indicators)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `fraud_detection_model.pkl not found` | Run `model.ipynb` first |
| `Invalid input` | Enter numeric values only (no text) |
| `Input file not found` | Check CSV filename and path |
| `ModuleNotFoundError: pandas` | Run `pip install -r requirements.txt` |
| All predictions are normal | Check feature ranges; may need model retraining |

---

## Examples

### Example 1: Normal Transaction
```
Customer ID: CUST001
Amount: 500
Old Balance Origin: 1000
New Balance Origin: 500
Old Balance Dest: 2000
New Balance Dest: 2500
```
✅ Result: Normal (1% fraud probability)

### Example 2: Suspicious Transaction
```
Customer ID: CUST999
Amount: 50000
Old Balance Origin: 100000
New Balance Origin: 50000
Old Balance Dest: 10000
New Balance Dest: 60000
```
Check error balances and probability...

---

## Support

For issues, check:
1. `README.md` for detailed documentation
2. Ensure model is trained (`fraud_detection_model.pkl` exists)
3. Verify Python 3.8+ installed
4. Confirm all dependencies installed: `pip install -r requirements.txt`
