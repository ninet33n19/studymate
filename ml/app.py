from flask import Flask, request, jsonify
from .storage import save_portfolio, load_portfolio
from .chatbot import process_query
import json
from datetime import datetime

app = Flask(__name__)

# Load the portfolio database from MongoDB (using the load_portfolio from storage.py)
portfolio_db = load_portfolio()

def createProfile(data):
    user_id = data.get("user_id")
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    
    # Check if user profile already exists
    if user_id in portfolio_db:
        return {"status": "error", "message": "User profile already exists"}
    
    # Initialize the calendar field if not present
    if "calendar" not in data:
        data["calendar"] = []

    portfolio_db[user_id] = data
    save_portfolio(portfolio_db)
    print("Current Portfolio DB (after creation):", portfolio_db)
    return {"status": "success", "message": "Profile created successfully", "data": data}

def updateProfile(user_id, updated_data):
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    if user_id not in portfolio_db:
        return {"status": "error", "message": "User profile not found"}
    
    # Initialize calendar if not present
    if "calendar" not in portfolio_db[user_id]:
        portfolio_db[user_id]["calendar"] = []
    
    portfolio_db[user_id].update(updated_data)
    if 'calendar' in updated_data:
        existing_calendar = portfolio_db[user_id].get('calendar', [])
        new_calendar_events = updated_data['calendar']
        existing_calendar.extend(new_calendar_events)
        portfolio_db[user_id]['calendar'] = existing_calendar
    
    save_portfolio(portfolio_db)
    print("Current Portfolio DB (after update):", portfolio_db)
    return {"status": "success", "message": "Profile updated successfully"}

def getProfile(user_id):
    if not user_id:
        return {"status": "error", "message": "User ID is required"}
    profile = portfolio_db.get(user_id)
    if not profile:
        return {"status": "error", "message": "User profile not found"}
    
    # Initialize calendar if not present
    if "calendar" not in profile:
        profile["calendar"] = []
    
    return {"status": "success", "data": profile}

def addRoadmap(user_id, prompt):
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    response = process_query(
        f"Generate a roadmap for me for the most efficient learning. Additional prompt by me: {prompt}. "
        f"Return a json array string which has keys as dates as , and value contains 'time', 'title','description'. "
        f"Do not respond in markdown, simply respond in plaintext. Use the current date ({current_date}) for events.",
        {"user_id": user_id}
    )
    a = response["generated_text"].strip().replace("```json", "").replace("```", "")
    roadmap = json.loads(a)
    return roadmap

@app.route('/portfolio/load', methods=['POST'])
def loadRoadmap():
    data = request.json
    user_id = data.get("user_id")
    prompts = data.get("prompts")
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is required"}), 400
    
    # Retrieve user profile
    profile = portfolio_db.get(user_id)
    if not profile:
        return jsonify({"status": "error", "message": "User profile not found"}), 404
    
    # Initialize the calendar if not present
    if "calendar" not in profile:
        profile["calendar"] = []
    
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Add the prompt events into the calendar
    if prompts:
        new_event = {
            "date": current_date,  # Use current date instead of static date
            "time": "10:00 AM",
            "title": "Exam",
            "description": f"Exam based on prompt: {prompts}",
        }
        profile["calendar"].append(new_event)

    # Save the updated profile with the new calendar event
    portfolio_db[user_id] = profile
    save_portfolio(portfolio_db)
    
    return jsonify({"status": "success", "message": "Roadmap loaded and updated", "calendar": profile["calendar"]}), 200

@app.route('/portfolio/mark_complete', methods=['POST'])
def markComplete():
    data = request.json
    user_id = data.get("user_id")
    date = data.get("date")
    
    if not user_id or not date:
        return jsonify({"status": "error", "message": "User ID and date are required"}), 400
    
    # Retrieve user profile
    profile = portfolio_db.get(user_id)
    if not profile:
        return jsonify({"status": "error", "message": "User profile not found"}), 404
    
    # Initialize calendar if not present
    if "calendar" not in profile:
        profile["calendar"] = []
    
    # Check if the event exists in the calendar
    calendar = profile.get("calendar", [])
    event = next((e for e in calendar if e["date"] == date), None)
    
    if not event:
        return jsonify({"status": "error", "message": "Event not found for the given date"}), 404
    
    # Mark the event as complete
    event["completed"] = True
    save_portfolio(portfolio_db)
    
    return jsonify({"status": "success", "message": "Event marked as complete", "data": event}), 200

@app.route('/portfolio/get_roadmap', methods=['GET'])
def getRoadmap():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "User ID is required"}), 400
    
    # Retrieve user profile
    profile = portfolio_db.get(user_id)
    if not profile:
        return jsonify({"status": "error", "message": "User profile not found"}), 404
    
    # Initialize the calendar if not present
    if "calendar" not in profile:
        profile["calendar"] = []
    
    # Fetch calendar
    calendar = profile.get("calendar", [])
    return jsonify({"status": "success", "data": calendar}), 200

if __name__ == "__main__":
    app.run(debug=True)
