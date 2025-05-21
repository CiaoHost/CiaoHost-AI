import json
import os
import uuid
from datetime import datetime

# Path to the JSON database file
DATABASE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "DatabaseCiaoHostProprieta.json")

def load_database():
    """Load the database from the JSON file"""
    if not os.path.exists(DATABASE_FILE):
        # Create a new database file if it doesn't exist
        initial_data = {
            "properties": {},
            "users": {}
        }
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        return initial_data
    
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # If the file is corrupted, create a new one
        initial_data = {
            "properties": {},
            "users": {}
        }
        with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        return initial_data

def save_database(data):
    """Save the database to the JSON file"""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_all_properties():
    """Get all properties from the database"""
    db = load_database()
    properties = []
    
    for prop_id, prop_data in db.get("properties", {}).items():
        # Convert the JSON property format to the format expected by the application
        property_data = {
            "id": prop_id,
            "name": prop_data.get("name", ""),
            "type": prop_data.get("type", ""),
            "city": prop_data.get("location", ""),
            "address": prop_data.get("address", ""),
            "bedrooms": prop_data.get("bedrooms", 1),
            "bathrooms": prop_data.get("bathrooms", 1),
            "max_guests": prop_data.get("max_guests", 2),
            "base_price": prop_data.get("price", 0),
            "cleaning_fee": prop_data.get("cleaning_fee", 30),
            "amenities": prop_data.get("services", []),
            "check_in_instructions": prop_data.get("check_in_instructions", ""),
            "wifi_details": prop_data.get("wifi_details", ""),
            "status": prop_data.get("status", "Attivo"),
            "phone": prop_data.get("phone", ""),
            "created_at": prop_data.get("created_at", datetime.now().isoformat()),
            "updated_at": prop_data.get("updated_at", datetime.now().isoformat())
        }
        properties.append(property_data)
    
    return properties

def get_property(property_id):
    """Get a property by ID"""
    db = load_database()
    prop_data = db.get("properties", {}).get(property_id)
    
    if not prop_data:
        return None
    
    # Convert the JSON property format to the format expected by the application
    property_data = {
        "id": property_id,
        "name": prop_data.get("name", ""),
        "type": prop_data.get("type", ""),
        "city": prop_data.get("location", ""),
        "address": prop_data.get("address", ""),
        "bedrooms": prop_data.get("bedrooms", 1),
        "bathrooms": prop_data.get("bathrooms", 1),
        "max_guests": prop_data.get("max_guests", 2),
        "base_price": prop_data.get("price", 0),
        "cleaning_fee": prop_data.get("cleaning_fee", 30),
        "amenities": prop_data.get("services", []),
        "check_in_instructions": prop_data.get("check_in_instructions", ""),
        "wifi_details": prop_data.get("wifi_details", ""),
        "status": prop_data.get("status", "Attivo"),
        "phone": prop_data.get("phone", ""),
        "created_at": prop_data.get("created_at", datetime.now().isoformat()),
        "updated_at": prop_data.get("updated_at", datetime.now().isoformat())
    }
    
    return property_data

def add_property(property_data):
    """Add a new property to the database"""
    db = load_database()
    
    # Generate a new ID if not provided
    property_id = property_data.get("id", str(uuid.uuid4()))
    
    # Convert the application property format to the JSON format
    json_property = {
        "name": property_data.get("name", ""),
        "type": property_data.get("type", ""),
        "location": property_data.get("city", ""),
        "address": property_data.get("address", ""),
        "bedrooms": property_data.get("bedrooms", 1),
        "bathrooms": property_data.get("bathrooms", 1),
        "max_guests": property_data.get("max_guests", 2),
        "price": property_data.get("base_price", 0),
        "cleaning_fee": property_data.get("cleaning_fee", 30),
        "services": property_data.get("amenities", []),
        "check_in_instructions": property_data.get("check_in_instructions", ""),
        "wifi_details": property_data.get("wifi_details", ""),
        "status": property_data.get("status", "Attivo"),
        "phone": property_data.get("phone", ""),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Add the property to the database
    db["properties"][property_id] = json_property
    
    # Save the database
    save_database(db)
    
    return True

def update_property(property_id, property_data):
    """Update an existing property in the database"""
    db = load_database()
    
    if property_id not in db.get("properties", {}):
        return False
    
    # Convert the application property format to the JSON format
    json_property = {
        "name": property_data.get("name", ""),
        "type": property_data.get("type", ""),
        "location": property_data.get("city", ""),
        "address": property_data.get("address", ""),
        "bedrooms": property_data.get("bedrooms", 1),
        "bathrooms": property_data.get("bathrooms", 1),
        "max_guests": property_data.get("max_guests", 2),
        "price": property_data.get("base_price", 0),
        "cleaning_fee": property_data.get("cleaning_fee", 30),
        "services": property_data.get("amenities", []),
        "check_in_instructions": property_data.get("check_in_instructions", ""),
        "wifi_details": property_data.get("wifi_details", ""),
        "status": property_data.get("status", "Attivo"),
        "phone": property_data.get("phone", ""),
        "created_at": property_data.get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat()
    }
    
    # Update the property in the database
    db["properties"][property_id] = json_property
    
    # Save the database
    save_database(db)
    
    return True

def delete_property(property_id):
    """Delete a property from the database"""
    db = load_database()
    
    if property_id not in db.get("properties", {}):
        return False
    
    # Delete the property from the database
    del db["properties"][property_id]
    
    # Save the database
    save_database(db)
    
    return True