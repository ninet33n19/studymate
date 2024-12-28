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
import dotenv
dotenv.load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
CORS(app)


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
    filename = file.filename
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    content_type, _ = mimetypes.guess_type(filename)
    file_size = len(file.read())
    file.seek(0)

    # Save the file locally
    file_path = os.path.join(LOCAL_FILES_DIR, filename)
    file.save(file_path)

    # Extract file metadata
    file_metadata = {
        "file_name": filename,
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
    user_id = request.form.get("user_id", "default_user")  # Provide default string value
    prompt = request.form.get("prompt", "")  # Provide default empty string

    if not file:
        return jsonify({"error": "File is required"}), 400

    response = test_extract_text_from_file(file, prompt=prompt, user_id=user_id)
    return jsonify({"response": response})

@app.route('/portfolio/create', methods=['POST'])
def create_profile():
    """ Code to create profile """
    data = request.json
    return createProfile(data)


@app.route('/portfolio/update', methods=['POST'])
def update_profile():
    """ Code to update profile """
    data = request.json
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    return updateProfile(user_id, data)



@app.route('/portfolio/roadmap', methods=['POST'])
def add_roadmap():
    try:
        data = request.get_json()
        print("Received request data:", data)

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        prompt = data.get("prompt")
        if not prompt:
            return jsonify({"error": "prompt is required"}), 400

        roadmap = addRoadmap(user_id, prompt, db=db, ROADMAP_COLLECTION=ROADMAP_COLLECTION)

        if not roadmap:
            return jsonify({"error": "Failed to generate roadmap"}), 500

        response_data = {
            "roadmap": roadmap,
            "message": "Roadmap generated successfully"
        }
        print("Sending response:", response_data)
        return jsonify(response_data), 200

    except Exception as e:
        print("Error in route:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/chatbot', methods=['POST'])
def chatbot():
    """
    API endpoint to process a query using the chatbot model.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    text = data.get("text")
    if not text:
        return jsonify({"error": "Text query is required"}), 400

    params = data.get("params", {})

    response = process_query(text, params)
    return jsonify({"response": response}), 200


@app.route('/call')
def call():
    # return jsonify({"response":"Turned off for credits"})
    tx=check_up_call("Swar")
    return jsonify({"response":tx})


@app.route('/user', methods=['GET'])
def get_profile():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    user_profile = db[USER_COLLECTION].find_one({"user_id": user_id})
    if not user_profile:
        return jsonify({"error": "User profile not found"}), 404

    #remove object id
    user_profile = {k: v for k, v in user_profile.items() if k != '_id'}
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
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    # Fetch the roadmaps from MongoDB for the provided user_id
    roadmaps = list(db[ROADMAP_COLLECTION].find({"user_id": user_id}))
    if not roadmaps:
        return jsonify({"roadmaps": []}), 200

    # Remove object IDs from the response
    roadmaps = [{"title": roadmap.get("title"), "roadmap": roadmap.get("roadmap")} for roadmap in roadmaps]

    return jsonify({"roadmaps": roadmaps}), 200


@app.route('/quiz', methods=['POST'])
def quiz():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    prompt = data.get("prompt", [])
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    num_questions = data.get("num_questions", 5)
    quiz = generate_quiz(prompt, user_id=user_id, num_questions=num_questions)

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
def generate_flashcards():
    try:
        file = request.files.get("file", None)
        text = request.form.get("text", None)
        user_id = request.form.get("user_id", None)

        if file:
            filename = file.filename
            if filename is None:
                return jsonify({"error": "Invalid filename"}), 400
            content_type, _ = mimetypes.guess_type(str(filename))
            extracted_text = extract_text_from_file(file, content_type)
        elif text:
            extracted_text = text
        else:
            return jsonify({"error": "Either a file or text content must be provided"}), 400

        # Generate structured flashcards using OpenAI
        prompt = f"""
        Create exactly 5 flashcards from this content. Return ONLY a JSON array of flashcards.
        Content: {extracted_text[:3000]}

        Format each flashcard as:
        {{
            "question": "Clear concise question",
            "answer": "Clear concise answer",
            "topic": "Topic of this flashcard"
        }}

        Return ONLY the JSON array, nothing else. Example:
        [
            {{
                "question": "What is...",
                "answer": "It is...",
                "topic": "Main concept"
            }},
            // more cards...
        ]
        """

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a flashcard generator. Always respond with valid JSON arrays containing flashcards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        # Extract and parse the response
        response_content = response.choices[0].message.content
        if response_content is None:
            raise ValueError("Empty response from OpenAI")

        response_text = response_content.strip()

        # Clean the response to ensure it's valid JSON
        if response_text.startswith('```json'):
            response_text = response_text.replace('```json', '').replace('```', '').strip()

        # Parse the JSON and validate the structure
        try:
            flashcards = json.loads(response_text)
            if not isinstance(flashcards, list):
                raise ValueError("Response is not a list")

            # Validate each flashcard
            for card in flashcards:
                if not all(key in card for key in ['question', 'answer', 'topic']):
                    raise ValueError("Invalid flashcard structure")

            print(f"Successfully generated {len(flashcards)} flashcards")
            return jsonify({"flashcards": flashcards}), 200

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            # Fallback: Create basic flashcards from the text
            fallback_flashcards = [
                {
                    "question": "What is the main topic of this document?",
                    "answer": extracted_text[:100] + "...",
                    "topic": "Overview"
                }
            ]
            return jsonify({"flashcards": fallback_flashcards}), 200

    except Exception as e:
        print(f"Error in generate_flashcards: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0")
