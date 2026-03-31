import pymongo

def setup_database():
    """Setup sample data in MongoDB for testing."""
    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["fraud_db"]
        customers = db["customers"]
        
        # Sample customer data
        sample_customers = [
            {
                "customer_id": "C123456789",
                "balance": 10000.0,
                "email": "sender@example.com",
                "phone": "+1234567890"
            },
            {
                "customer_id": "C987654321",
                "balance": 5000.0,
                "email": "receiver@example.com",
                "phone": "+0987654321"
            },
            {
                "customer_id": "C111111111",
                "balance": 20000.0,
                "email": "user1@example.com",
                "phone": "+1111111111"
            }
        ]
        
        # Insert sample data
        customers.insert_many(sample_customers)
        print("✅ Sample customer data inserted into MongoDB.")
        
        # Verify
        count = customers.count_documents({})
        print(f"Total customers in database: {count}")
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")

if __name__ == "__main__":
    setup_database()