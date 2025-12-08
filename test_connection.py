"""
Test MongoDB connection script
Run this to verify your MongoDB Atlas connection is working
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

def test_connection():
    """Test MongoDB connection"""
    load_dotenv()
    
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("ERROR: MONGODB_URI not found in .env file")
        return False
    
    if "<db_username>" in mongodb_uri or "<db_password>" in mongodb_uri:
        print("WARNING: Please replace <db_username> and <db_password> in .env file with your actual credentials")
        return False
    
    try:
        print("Attempting to connect to MongoDB Atlas...")
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Test database access
        db = client["library"]
        collections = db.list_collection_names()
        print(f"✅ Database 'library' is accessible")
        print(f"   Collections found: {len(collections)}")
        if collections:
            print(f"   Collection names: {', '.join(collections)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check that <db_username> and <db_password> are replaced with your actual credentials")
        print("2. Verify your IP address is whitelisted in MongoDB Atlas")
        print("3. Check your network connection")
        return False

if __name__ == "__main__":
    test_connection()

