from flask import Flask, request, jsonify
from new_final import DocumentProcessor, ChatResponse  # Assuming your code is in a file named `document_processor.py`

app = Flask(__name__)

# Initialize DocumentProcessor with MongoDB URI
document_processor = DocumentProcessor(mongodb_uri="mongodb://localhost:27017/")

@app.route('/process-document', methods=['POST'])
def process_document():
    try:
        file_path = request.json.get('file_path')
        user_id = request.json.get('user_id')
        if not file_path or not user_id:
            return jsonify({"error": "file_path and user_id are required"}), 400
        
        doc_id = document_processor.process_document(file_path, user_id)
        return jsonify({"message": "Document processed successfully", "doc_id": doc_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        query = request.json.get('query')
        user_id = request.json.get('user_id')
        if not query or not user_id:
            return jsonify({"error": "query and user_id are required"}), 400
        
        response: ChatResponse = document_processor.process_query(query, user_id)
        return jsonify({
            "answer": response.answer,
            "sources": response.sources,
            "query_type": response.query_type,
            "confidence": response.confidence
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
