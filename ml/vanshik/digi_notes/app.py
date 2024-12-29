from flask import Flask, request, jsonify, Response
from werkzeug.utils import secure_filename
import PyPDF2
import pytesseract
from PIL import Image
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from datetime import datetime
import logging
import re
import io
import spacy
from typing import Dict, List, Optional, Tuple

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Download required NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Configuration
class Config:
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    PORT = 8000

# Load pre-trained SpaCy model
nlp = spacy.load('en_core_web_sm')

class TextProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?]', '', text)
        return text.strip()

    @staticmethod
    def get_important_sentences(sentences: List[str], num_sentences: int = 10) -> List[str]:
        """Select important sentences based on length and content."""
        meaningful_sentences = []
        for sentence in sentences:
            if len(sentence.split()) > 5:
                tagged = pos_tag(word_tokenize(sentence))
                if any(tag.startswith('VB') for word, tag in tagged):
                    meaningful_sentences.append(sentence)
        
        return meaningful_sentences[:num_sentences]

class DocumentProcessor:
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        try:
            text = ""
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return TextProcessor.clean_text(text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise

    @staticmethod
    def extract_text_from_image(image_file) -> str:
        try:
            image = Image.open(image_file)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image = image.resize((image.width * 2, image.height * 2))
            text = pytesseract.image_to_string(image)
            return TextProcessor.clean_text(text)
        except Exception as e:
            logger.error(f"Error extracting text from image: {str(e)}")
            raise

class ContentGenerator:
    def __init__(self, text: str):
        self.text = text
        self.sentences = sent_tokenize(text)
        self.important_sentences = TextProcessor.get_important_sentences(self.sentences)

    def generate_study_question(self, sentence: str) -> str:
        """Generate a structured study question from a sentence."""
        doc = nlp(sentence)
        subject = None
        verb = None
        object_ = None
        
        for token in doc:
            if 'subj' in token.dep_:
                subject = token.text
            if token.dep_ == 'ROOT':
                verb = token.text
            if 'obj' in token.dep_:
                object_ = token.text
        
        if subject and verb and object_:
            return f"What does {subject} {verb} in relation to {object_}?"
        elif subject and verb:
            return f"What does {subject} {verb}?"
        elif verb and object_:
            return f"How does {object_} affect {verb}?"
        else:
            return f"What is {sentence}?"

    def generate_study_guide(self) -> List[Dict[str, str]]:
        """Generate study guide with only questions."""
        return [{"question": self.generate_study_question(sentence)} 
                for sentence in self.important_sentences[:10]]

    def generate_faq(self) -> List[Dict[str, str]]:
        """Generate FAQ from content."""
        question_templates = [
            "What are the key aspects of {}?",
            "How does {} work?",
            "Why is {} significant?",
            "Can you explain {}?",
            "What's important to know about {}?"
        ]
        
        return [{
            "question": question_templates[i % len(question_templates)].format(
                self._extract_topic(sentence)),
            "answer": sentence,
            "category": "Main Concepts" if i < 4 else "Additional Information"
        } for i, sentence in enumerate(self.important_sentences[:8])]

    def generate_brief(self) -> Dict[str, any]:
        """Generate a comprehensive brief."""
        top_sentences = self.important_sentences[:5]
        return {
            "summary": " ".join(top_sentences),
            "key_points": [{"point": sent, "index": i+1} 
                          for i, sent in enumerate(top_sentences)],
            "document_stats": {
                "total_paragraphs": len(self.text.split('\n\n')),
                "total_sentences": len(self.sentences),
                "estimated_reading_time": len(self.text.split()) // 200
            },
            "timestamp": datetime.now().isoformat()
        }

    def _extract_topic(self, sentence: str) -> str:
        """Extract the main topic from a sentence."""
        words = word_tokenize(sentence)
        tagged = pos_tag(words)
        nouns = [word for word, tag in tagged if tag.startswith('NN')]
        return nouns[0] if nouns else words[0]

@app.route('/')
def home():
    return jsonify({
        "status": "active",
        "endpoints": {
            "upload": "/upload",
            "health": "/health"
        },
        "supported_formats": list(Config.ALLOWED_EXTENSIONS)
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": f"Only {', '.join(Config.ALLOWED_EXTENSIONS)} files are allowed"}), 400
        
        # Process file in memory
        if file.filename.lower().endswith('.pdf'):
            text = DocumentProcessor.extract_text_from_pdf(file)
        else:
            text = DocumentProcessor.extract_text_from_image(file)
        
        if not text.strip():
            return jsonify({"error": "Could not extract text from the file"}), 400
        
        # Generate content
        generator = ContentGenerator(text)
        
        # Generate all content types
        output = {
            "study_guide": generator.generate_study_guide(),
            "faq": generator.generate_faq(),
            "brief": generator.generate_brief()
        }
        
        return jsonify(output)

    except Exception as e:
        logger.error(f"Error during file processing: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "The API is up and running!"
    })

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)