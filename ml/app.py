import os
import mimetypes
import openai
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from datetime import datetime
from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
import docx2txt
from flask_cors import CORS
from langchain_openai import OpenAIEmbeddings
import json
from uitils.extraction import extract_text_from_file, extract_doctype_from_file, extract_embeddings_from_file, extract_keywords_from_file, extract_chapter_name_subject, extract_syllabus_or_date_changes
from uitils.portfolio import createProfile, updateProfile, addRoadmap
from uitils.chatbot import process_query, check_up_call,generate_quiz,generate_openai
from pymongo import MongoClient
from uitils.test import test_extract_text_from_file
from uitils.courses import generate_course
from uitils.flashcards import SimpleFlashcardGenerator
import dotenv
dotenv.load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
CORS(app)
# Initialize NLP
# nlp = spacy.load("en_core_web_sm")


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client['RGIT_DB']
FILES_COLLECTION = "files"
METADATA_COLLECTION = "metadata"
USER_COLLECTION = "users"
ROADMAP_COLLECTION="roadmap"
# Set up local storage directories
LOCAL_FILES_DIR = "./files"
LOCAL_METADATA_DIR = "./metadata"
os.makedirs(LOCAL_FILES_DIR, exist_ok=True)
os.makedirs(LOCAL_METADATA_DIR, exist_ok=True)

# Load environment variables (e.g., OpenAI API key)
openai.api_key = os.getenv("OPENAI_API_KEY")


@app.route('/upload', methods=['POST'])
def upload_document():
    """
    API endpoint to upload a file, extract metadata and content, and store in local storage.
    """
    user_id = request.form.get("user_id")
    file = request.files.get("file")

    if not user_id or not file:
        return jsonify({"error": "User ID and file are required"}), 400

    # Detect content type of the file
    content_type, _ = mimetypes.guess_type(file.filename)
    file_size = len(file.read())
    file.seek(0)

    # Save the file locally
    file_path = os.path.join(LOCAL_FILES_DIR, file.filename)
    file.save(file_path)

    # Extract file metadata
    file_metadata = {
        "file_name": file.filename,
        "file_type": content_type,
        "upload_date": datetime.utcnow().isoformat(),
        "file_size": file_size,
        "page_count": None  # Can be extracted for PDFs or DOCX if needed
    }

    # Extract text from the file
    extracted_text = extract_text_from_file(file, content_type)

    # Generate embeddings
    embeddings = extract_embeddings_from_file(extracted_text)

    # Extract keywords/topics from the document
    keywords = extract_keywords_from_file(extracted_text)

    # Classify the document (study material, announcement, etc.)
    doc_type = extract_doctype_from_file(extracted_text)

    # Extract chapter name and subject if study material
    chapter_info = None
    if doc_type == "STUDY_MATERIAL":
        chapter_info = extract_chapter_name_subject(extracted_text,user_id)
        

    # Extract syllabus or date changes if announcement
    announcement_info = None
    if doc_type == "ANNOUNCEMENT":
        announcement_info = extract_syllabus_or_date_changes(extracted_text,user_id)
        #### TODO Trigger portfolio updation here ( /portfolio/update)

    # Document content structure
    document_content = {
        "extracted_text": extracted_text,
        "embeddings": embeddings,
        "key_topics": keywords,
       # This could be more advanced NER if required
    }

    # Classification structure
    classification = {
        "document_type": doc_type,
        "subject": chapter_info.get("subject") if chapter_info else None,
        "chapter_name": chapter_info.get("chapter") if chapter_info else None,
        "syllabus_or_date_changes": announcement_info if doc_type == "ANNOUNCEMENT" else None
    }
    metadata_doc = {
        "user_id": user_id,
        "file_metadata": file_metadata,
        "document_content": document_content,
        "classification": classification
    }

    # Save metadata and content to a JSON file
    metadata_id = db[METADATA_COLLECTION].insert_one(metadata_doc).inserted_id

    return jsonify({"message": "File uploaded and processed successfully"}), 200



@app.route('/test', methods=['POST'])
def solve_test():
    file = request.files.get("file")
    user_id = request.form.get("user_id",None)
    prompt =request.form.get("prompt",None)
    response=test_extract_text_from_file(file,prompt=prompt,user_id=user_id)
    return jsonify({"response":response})

@app.route('/portfolio/create', methods=['POST'])
def create_profile():
    """ Code to create profile """
    data = request.json
    return createProfile(data)
    

@app.route('/portfolio/update', methods=['POST'])
def update_profile():
    """ Code to update profile """
    data = request.json
    return updateProfile(data['user_id'],data)



@app.route('/portfolio/roadmap', methods=['POST'])
def add_roadmap():
    user_id = request.json.get("user_id", "user_1")
    prompt = request.json.get("prompt",None)
    
    """ Code to create roadmap """
    return addRoadmap(user_id,prompt)
    
@app.route('/chatbot', methods=['POST'])
def chatbot():
    """
    API endpoint to process a query using the chatbot model.
    """
    data = request.json
    text = data.get("text")
    params = data.get("params", {})

    response = process_query(text, params)
    return jsonify({"response": response}), 200


@app.route('/call', methods=['POST'])
def call():
    # Extract the JSON body
    data = request.get_json()
    if not data or 'name' not in data or 'phone_number' not in data:
        return jsonify({"error": "Please provide both 'name' and 'phone_number' in the request body"}), 400

    student_name = data['name']
    phone_number = data['phone_number']

    # Call the function with dynamic inputs
    tx = check_up_call(student_name, phone_number)
    return jsonify({"response": tx})

@app.route('/interview', methods=['POST'])
def interview_call():
    # Extract JSON input
    data = request.get_json()
    if not data or 'name' not in data or 'phone_number' not in data:
        return jsonify({"error": "Please provide both 'name' and 'phone_number' in the request body"}), 400

    student_name = data['name']
    phone_number = data['phone_number']

    # Call the function with dynamic inputs
    tx = interview_call(student_name, phone_number)  # Pass both arguments here
    return jsonify({"response": tx})

    # Call the function with dy


@app.route('/user', methods=['GET'])
def get_profile():
    user_id = request.args.get("user_id")
    user_profile = db[USER_COLLECTION].find_one({"user_id": user_id})
    #remove object id
    user_profile={k: v for k, v in user_profile.items() if k != '_id'}
    return jsonify({"profile": user_profile}), 200

@app.route('/user/document', methods=['GET'])
def get_user_documents():
    user_id = request.args.get("user_id")
    documents = db[METADATA_COLLECTION].find({"user_id": user_id})
    
    #remove object id
    documents=[{k: v for k, v in doc.items() if k != '_id'} for doc in documents]
    
    return jsonify({"documents": list(documents)}), 200

@app.route('/load-roadmaps', methods=['POST'])
def load_roadmaps():
    user_id = request.json.get("user_id")
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Fetch the roadmaps from MongoDB for the provided user_id
    roadmaps = db[ROADMAP_COLLECTION].find({"user_id": user_id})
    
    # Remove object IDs from the response
    roadmaps = [{"title": roadmap["title"], "roadmap": roadmap["roadmap"]} for roadmap in roadmaps]
    
    return jsonify({"roadmaps": roadmaps}), 200


@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.json
    prompt = data.get("prompt",[])
    user_id = data.get("user_id")
    quiz= generate_quiz(prompt,user_id=user_id,num_questions=data.get("num_questions",5))
    return jsonify({"response": quiz}), 200

@app.route('/course', methods=['POST'])
def generate_course_endpoint():
    try:
        # Get file from the request
        file = request.files['file']
        
        # Generate course content
        course_content = generate_course(file)
        
        # Return the JSON response
        return jsonify(course_content)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/flashcards', methods=['POST'])
def generate_flashcard_endpoint():
    try:
        # Get the folder path from the request
        data = request.get_json()  # Receive the JSON data
        folder_path = data.get('folder_path')  # Get the folder path from the JSON

        if not folder_path:
            return jsonify({"error": "No folder path provided"}), 400
        
        # Initialize the flashcard generator with your API key
        api_key = os.getenv('API_KEY')  # Ensure the API key is set in your environment
        flashcard_generator = SimpleFlashcardGenerator(api_key)

        # Process the PDFs in the provided folder and generate flashcards
        result = flashcard_generator.process_pdfs(folder_path)

        # Return the generated flashcards and summary
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
