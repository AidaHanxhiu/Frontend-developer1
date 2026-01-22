# Import ObjectId for MongoDB document ID handling
from bson import ObjectId

# Import datetime to store timestamps
from datetime import datetime


# ------------------------------
# Database connection helper
# ------------------------------
def get_db():
    """Get database connection"""

    # Import MongoDB client
    from pymongo import MongoClient

    # Import OS module to access environment variables
    import os

    # Import dotenv to load .env file variables
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # Read MongoDB URI from environment variables
    mongodb_uri = os.getenv("MONGODB_URI")

    # Raise error if MongoDB URI is not set
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is not set. Please check your .env file.")

    # Remove quotes if URI is wrapped in quotes
    mongodb_uri = mongodb_uri.strip().strip('"').strip("'")

    # Create MongoDB client with a timeout
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)

    # Return the "library" database
    return client["library"]


# ------------------------------
# CREATE AUTHOR
# ------------------------------
def create_author(name, bio=None):
    """Create a new author"""

    # Get database connection
    db = get_db()
    
    # Check if an author with the same name already exists
    existing = db.authors.find_one({"name": name})

    # If author exists, return the existing document
    if existing:
        return existing
    
    # Create author document
    author = {
        "name": name,                          # Author name
        "bio": bio,                            # Author biography (optional)
        "created_at": datetime.utcnow()        # Timestamp of creation
    }
    
    # Insert author into the authors collection
    result = db.authors.insert_one(author)

    # Attach generated ObjectId to author object
    author["_id"] = result.inserted_id

    # Return the newly created author
    return author


# ------------------------------
# PUBLISHERS (NEW CLASS)
# ------------------------------
# TODO: adjust fields (name, country, year_founded, description, etc.) as needed.
def create_publisher(data):
    """Create a new publisher"""

    # Get database connection
    db = get_db()

    # Extract publisher name from input data
    name = data.get("name")

    # Validate that name is provided
    if not name:
        raise ValueError("Publisher 'name' is required")

    # Check if publisher already exists
    existing = db.publishers.find_one({"name": name})

    # If publisher exists, return it
    if existing:
        return existing

    # Create publisher document
    publisher = {
        "name": name,                           # Publisher name
        "country": data.get("country"),         # Publisher country
        "year_founded": data.get("year_founded"),  # Year founded
        "description": data.get("description"), # Publisher description
        "created_at": datetime.utcnow()         # Timestamp of creation
    }

    # Insert publisher into database
    result = db.publishers.insert_one(publisher)

    # Attach generated ObjectId
    publisher["_id"] = result.inserted_id

    # Return the created publisher
    return publisher


def get_all_publishers():
    """Get all publishers"""

    # Get database connection
    db = get_db()

    # Return list of all publishers
    return list(db.publishers.find({}))


def get_publisher_by_id(publisher_id):
    """Get publisher by ID"""

    # Get database connection
    db = get_db()

    try:
        # Convert string ID to ObjectId and fetch publisher
        return db.publishers.find_one({"_id": ObjectId(publisher_id)})
    except:
        # Return None if ID is invalid
        return None


def update_publisher(publisher_id, update_data):
    """Update publisher information"""

    # Get database connection
    db = get_db()

    try:
        # Update publisher document using $set
        result = db.publishers.update_one(
            {"_id": ObjectId(publisher_id)},
            {"$set": update_data}
        )

        # Return True if a document was modified
        return result.modified_count > 0
    except:
        # Return False if update fails
        return False


def delete_publisher(publisher_id):
    """Delete a publisher"""

    # Get database connection
    db = get_db()

    try:
        # Delete publisher by ObjectId
        result = db.publishers.delete_one({"_id": ObjectId(publisher_id)})

        # Return True if deletion was successful
        return result.deleted_count > 0
    except:
        # Return False if deletion fails
        return False


# ------------------------------
# READ AUTHORS
# ------------------------------
def get_all_authors():
    """Get all authors"""

    # Get database connection
    db = get_db()

    # Return list of all authors
    return list(db.authors.find({}))


def get_author_by_id(author_id):
    """Get author by ID"""

    # Get database connection
    db = get_db()

    try:
        # Convert string ID to ObjectId and fetch author
        return db.authors.find_one({"_id": ObjectId(author_id)})
    except:
        # Return None if ID is invalid
        return None


def get_author_by_name(name):
    """Get author by name"""

    # Get database connection
    db = get_db()

    # Find author by name
    return db.authors.find_one({"name": name})


# ------------------------------
# UPDATE AUTHOR
# ------------------------------
def update_author(author_id, update_data):
    """Update author information"""

    # Get database connection
    db = get_db()

    try:
        # Update author document
        result = db.authors.update_one(
            {"_id": ObjectId(author_id)},
            {"$set": update_data}
        )

        # Return True if update was successful
        return result.modified_count > 0
    except:
        # Return False if update fails
        return False


# ------------------------------
# DELETE AUTHOR
# ------------------------------
def delete_author(author_id):
    """Delete an author"""

    # Get database connection
    db = get_db()

    try:
        # Delete author by ObjectId
        result = db.authors.delete_one({"_id": ObjectId(author_id)})

        # Return True if deletion was successful
        return result.deleted_count > 0
    except:
        # Return False if deletion fails
        return False
