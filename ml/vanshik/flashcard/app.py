import os
from flask import Flask, request, jsonify, send_file
from pathlib import Path
import json
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from flashcard2 import EnhancedFlashcardGenerator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf'}
    BASE_DIR = Path(__file__).parent.resolve()
    UPLOADS_DIR = BASE_DIR / "uploads"
    OUTPUTS_DIR = BASE_DIR / "outputs"
    ALLOWED_EXTENSIONS = {'pdf'}

# Create necessary directories
Config.UPLOADS_DIR.mkdir(exist_ok=True)
Config.OUTPUTS_DIR.mkdir(exist_ok=True)

# Initialize the flashcard generator
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

generator = EnhancedFlashcardGenerator(API_KEY)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def create_response(success: bool, message: str, data: dict = None, error: str = None):
    """Create a standardized response format."""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
    }
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify(create_response(
        success=True,
        message="Service is healthy",
        data={"status": "ok"}
    ))

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Handle PDF file upload."""
    try:
        if 'file' not in request.files:
            return jsonify(create_response(
                success=False,
                message="No file part in the request",
                error="missing_file"
            )), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify(create_response(
                success=False,
                message="No selected file",
                error="empty_filename"
            )), 400

        if not allowed_file(file.filename):
            return jsonify(create_response(
                success=False,
                message="File type not allowed",
                error="invalid_file_type"
            )), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        file_path = Config.UPLOADS_DIR / safe_filename
        
        file.save(file_path)

        return jsonify(create_response(
            success=True,
            message="File uploaded successfully",
            data={
                "file_name": safe_filename,
                "original_name": filename,
                "file_size": os.path.getsize(file_path),
                "upload_time": timestamp
            }
        ))

    except Exception as e:
        return jsonify(create_response(
            success=False,
            message="File upload failed",
            error=str(e)
        )), 500

@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards():
    """Generate flashcards from uploaded PDF."""
    try:
        file_name = request.form.get('file_name')
        if not file_name:
            return jsonify(create_response(
                success=False,
                message="No file name provided",
                error="missing_filename"
            )), 400

        pdf_path = Config.UPLOADS_DIR / file_name
        if not pdf_path.exists():
            return jsonify(create_response(
                success=False,
                message=f"File '{file_name}' not found",
                error="file_not_found"
            )), 404

        result = generator.process_pdf(str(pdf_path))
        
        if result["status"] == "success" and result["flashcards"]:
            # Create timestamped output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{pdf_path.stem}_{timestamp}_flashcards.json"
            output_path = Config.OUTPUTS_DIR / output_filename
            
            # Save flashcards to file
            with output_path.open("w") as f:
                json.dump(result, f, indent=2)

            return jsonify(create_response(
                success=True,
                message="Flashcards generated successfully",
                data={
                    "output_file": output_filename,
                    "flashcard_count": len(result["flashcards"]),
                    "metadata": result["metadata"]
                }
            ))
        else:
            return jsonify(create_response(
                success=False,
                message="Flashcard generation failed",
                error=result.get("error", "No flashcards generated")
            )), 422

    except Exception as e:
        return jsonify(create_response(
            success=False,
            message="Flashcard generation failed",
            error=str(e)
        )), 500

@app.route('/download-flashcards/<filename>', methods=['GET'])
def download_flashcards(filename):
    """Download generated flashcards JSON file."""
    try:
        file_path = Config.OUTPUTS_DIR / filename
        if not file_path.exists():
            return jsonify(create_response(
                success=False,
                message="Flashcards file not found",
                error="file_not_found"
            )), 404

        return send_file(
            file_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify(create_response(
            success=False,
            message="File download failed",
            error=str(e)
        )), 500

@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """Clean up old uploaded files and generated flashcards."""
    try:
        # Remove all files in uploads and outputs directories
        for file in Config.UPLOADS_DIR.glob('*'):
            file.unlink()
        for file in Config.OUTPUTS_DIR.glob('*'):
            file.unlink()

        return jsonify(create_response(
            success=True,
            message="Cleanup completed successfully",
            data={
                "cleaned_directories": [
                    str(Config.UPLOADS_DIR),
                    str(Config.OUTPUTS_DIR)
                ]
            }
        ))

    except Exception as e:
        return jsonify(create_response(
            success=False,
            message="Cleanup failed",
            error=str(e)
        )), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    return jsonify(create_response(
        success=False,
        message="File too large",
        error="file_too_large"
    )), 413

if __name__ == "__main__":
    app.run(debug=True)