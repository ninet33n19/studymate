from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import PyPDF2
import pytesseract
from PIL import Image

app = Flask(__name__)

# Get the directory of the current script and set the paths for uploads and outputs
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the folder where this script is located
UPLOAD_FOLDER = os.path.join(BASE_DIR,  'uploads')  # Save uploads in the 'digi_notes/uploads' folder
OUTPUT_FOLDER = os.path.join(BASE_DIR,  'outputs')  # Save outputs in the 'digi_notes/outputs' folder

# Create the directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """Check if the uploaded file is of an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_text_from_image(image_path):
    """Extract text from image using OCR."""
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return text
    except Exception as e:
        print(f"Error reading image: {e}")
        return ""

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process the file."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        # Generate a secure file name and save it to the 'uploads' folder
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Extract text from the uploaded file
        text = ""
        if filename.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(file_path)

        if not text.strip():
            return jsonify({"status": "error", "message": "Could not extract text"}), 500

        # Save extracted text to a new file in the 'outputs' folder
        output_filename = f"{os.path.splitext(filename)[0]}_notes.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, 'w') as output_file:
            output_file.write(text)

        # Return the download URL for the user to download the generated notes
        return jsonify({
            "status": "success",
            "message": "File processed successfully",
            "download_url": f"/download/{output_filename}"
        }), 200
    
    return jsonify({"status": "error", "message": "File type not allowed"}), 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """Allow the user to download the generated file."""
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({"status": "error", "message": "File not found"}), 404

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to ensure the app is running."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
