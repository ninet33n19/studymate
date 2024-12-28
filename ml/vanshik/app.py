from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from typing import Optional
from enhanced_rag_chatbot import EnhancedRAGChatbot, UserProfile  # Import your chatbot class
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
GOOGLE_API_KEY = "your-google-api-key"  # Replace with your API key

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global chatbot instance
chatbot_instance = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/initialize', methods=['POST'])
def initialize_chatbot():
    try:
        data = request.json
        
        # Create UserProfile from request data
        user_profile = UserProfile(
            user_id=data.get('user_id', 'default_user'),
            name=data.get('name', 'Default User'),
            course=data.get('course', ''),
            year=int(data.get('year', 1)),
            semester=int(data.get('semester', 1)),
            subjects=data.get('subjects', []),
            syllabus=data.get('syllabus', {})
        )
        
        global chatbot_instance
        # Initialize with a temporary document path - will be updated when document is uploaded
        chatbot_instance = EnhancedRAGChatbot(
            document_path="temp",
            google_api_key=GOOGLE_API_KEY,
            user_profile=user_profile
        )
        
        return jsonify({
            "status": "success",
            "message": "Chatbot initialized successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error initializing chatbot: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to initialize chatbot: {str(e)}"
        }), 500

@app.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file part"
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "No selected file"
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            global chatbot_instance
            if chatbot_instance is None:
                return jsonify({
                    "status": "error",
                    "message": "Chatbot not initialized"
                }), 400
            
            success, message = chatbot_instance.load_and_process_document(filepath)
            
            if success:
                return jsonify({
                    "status": "success",
                    "message": f"File processed successfully: {message}",
                    "filename": filename
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Failed to process file: {message}"
                }), 500
                
        except Exception as e:
            logger.error(f"Error processing uploaded file: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            }), 500
    
    return jsonify({
        "status": "error",
        "message": "File type not allowed"
    }), 400

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({
                "status": "error",
                "message": "No question provided"
            }), 400
        
        if chatbot_instance is None:
            return jsonify({
                "status": "error",
                "message": "Chatbot not initialized"
            }), 400
        
        response = chatbot_instance.chat(question)
        
        return jsonify({
            "status": "success",
            "response": response
        }), 200
        
    except Exception as e:
        logger.error(f"Error during chat: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error during chat: {str(e)}"
        }), 500

@app.route('/reset', methods=['POST'])
def reset_chatbot():
    try:
        global chatbot_instance
        chatbot_instance = None
        
        # Clean up uploaded files
        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {str(e)}")
        
        return jsonify({
            "status": "success",
            "message": "Chatbot reset successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting chatbot: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error resetting chatbot: {str(e)}"
        }), 500

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "chatbot_initialized": chatbot_instance is not None
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)