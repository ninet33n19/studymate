from .storage import save_portfolio, load_portfolio
from .chatbot import process_query,generate_openai
import json
from datetime import datetime  # Import datetime library
from pymongo import MongoClient  # Import MongoClient for MongoDB integration
from dotenv import load_dotenv  # Import dotenv to load environment variables
import os
# Load the portfolio database from MongoDB (using the load_portfolio from storage.py)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
if not MONGO_URI:
    raise ValueError("MongoDB URI is not defined in the .env file")
# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client["RGIT_DB"]  # Replace with your database name
roadmap_collection = db["roadmap"]  # Roadmap collection name


portfolio_db = load_portfolio()

def createProfile(data):
    """
    Function to create a new profile.
    
    Args:
        data (dict): Dictionary containing user profile information.
    
    Returns:
        dict: Result message (success or error).
    """
    user_id = data.get("user_id")
    
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    
    # Check if the profile already exists
    if user_id in portfolio_db:
        return {"status": "error", "message": "User profile already exists"}
    
    # Save the profile to MongoDB
    portfolio_db[user_id] = data  # Store it in the in-memory database
    save_portfolio(portfolio_db)  # Save to MongoDB
    
    # Debugging output to confirm storage in memory
    print("Current Portfolio DB (after creation):", portfolio_db)  
    
    return {"status": "success", "message": "Profile created successfully", "data": data}

def updateProfile(user_id, updated_data):
 
    if not user_id:
         return {"status": "error", "message": "User ID is required"}
    
    # Check if the profile exists
    if user_id not in portfolio_db:
        return {"status": "error", "message": "User profile not found"}
    
    # Update the profile with new data in-memory
    portfolio_db[user_id].update(updated_data)

    # Manage calendar updates
    if 'calendar' in updated_data:
        # Append new calendar events
        existing_calendar = portfolio_db[user_id].get('calendar', [])
        new_calendar_events = updated_data['calendar']
        existing_calendar.extend(new_calendar_events)
        portfolio_db[user_id]['calendar'] = existing_calendar

    # Save the updated profile to MongoDB
    save_portfolio(portfolio_db)  # Save updated data to MongoDB

    # Debugging output to confirm storage after update
    print("Current Portfolio DB (after update):", portfolio_db)  

    return {"status": "success", "message": "Profile updated successfully"}

def getProfile(user_id):
    """
    Function to get an existing profile by user_id.
    
    Args:
        user_id (str): Unique identifier of the user.
    
    Returns:
        dict: User profile if found, or an error message.
    """
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    
    # Retrieve the profile from the in-memory database
    profile = portfolio_db.get(user_id)
    
    if not profile:
        return {"status": "error", "message": "User profile not found"}
    
    return {"status": "success", "data": profile}


def addRoadmap(user_id,prompt):
        
    today_date = datetime.now().strftime("%Y-%m-%d")
    roadmap = process_query(f"Generate a roadmap for me for the most efficient learning. Additional prompt by me: {prompt} Return a json array string which has keys as dates, and value contains 'time', 'title','description'. Do not respond in markdown, simply respond in plaintext. Today's date is {today_date}. Return all the milestones with the key 'milestones'", {"user_id": user_id})["generated_text"].strip().replace("json", "").replace("", "")
    roadmap=json.loads(roadmap)
    #get title
    roadmap_title = generate_openai(f"Generate a title for the roadmap. The prompt by the user is {prompt}")
    
    # Save the roadmap to MongoDB
    roadmap_collection.insert_one({"user_id": user_id, "roadmap": roadmap,"title": roadmap_title})
    return roadmap