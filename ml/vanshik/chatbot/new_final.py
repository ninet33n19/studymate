import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
from bson.objectid import ObjectId
from io import BytesIO
import json
import numpy as np
from pymongo import MongoClient
from bson.binary import Binary
import pytesseract
from PIL import Image
import cv2
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import spacy
import fitz  # PyMuPDF
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueryType(Enum):
    STUDY = "study"
    GENERAL = "general"
    DOCUMENT = "document"

@dataclass
class ChatResponse:
    answer: str
    sources: List[Dict]
    query_type: str
    confidence: float

@dataclass
class ProcessedDocument:
    doc_id: str
    title: str
    content: str
    chunks: List[Dict]
    metadata: Dict
    embeddings: List[List[float]]
    timestamp: datetime

class DocumentProcessor:
    def __init__(self, mongodb_uri: str):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client['study_platform_db']
        self.docs_collection = self.db['documents']
        self.chunks_collection = self.db['chunks']
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        self.nlp = spacy.load("en_core_web_sm")

    def process_document(self, file_path: str, user_id: str) -> str:
        """Process a document and store it in MongoDB"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()

            if file_extension == '.pdf':
                return self._process_pdf(file_path, user_id)
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                return self._process_image(file_path, user_id)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def _process_pdf(self, file_path: str, user_id: str) -> str:
        """Process PDF document"""
        doc = fitz.open(file_path)
        doc_content = ""
        chunks = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            doc_content += text

            # Extract any images on the page and process with OCR
            for img_index, img in enumerate(page.get_images()):
                try:
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Process image with OCR
                    pil_image = Image.open(BytesIO(image_bytes))
                    ocr_text = self._perform_ocr(pil_image)
                    if ocr_text:
                        doc_content += f"\n{ocr_text}\n"
                except Exception as e:
                    logger.warning(f"Error processing image in PDF: {str(e)}")

        # Create chunks
        text_chunks = self._create_chunks(doc_content)

        # Generate embeddings
        embeddings = []
        for chunk in text_chunks:
            chunk_embedding = self.embeddings_model.embed_query(chunk)
            embeddings.append(chunk_embedding)

            chunks.append({
                "content": chunk,
                "embedding": chunk_embedding,
                "metadata": {
                    "source": file_path,
                    "type": "pdf",
                    "timestamp": datetime.utcnow()
                }
            })

        # Store in MongoDB
        doc_id = self._store_document(
            title=os.path.basename(file_path),
            content=doc_content,
            chunks=chunks,
            user_id=user_id,
            doc_type="pdf"
        )

        return doc_id

    def _process_image(self, file_path: str, user_id: str) -> str:
        """Process image document"""
        try:
            image = Image.open(file_path)
            extracted_text = self._perform_ocr(image)

            if not extracted_text:
                raise ValueError("No text extracted from image")

            # Create chunks
            text_chunks = self._create_chunks(extracted_text)

            # Generate embeddings
            chunks = []
            embeddings = []
            for chunk in text_chunks:
                chunk_embedding = self.embeddings_model.embed_query(chunk)
                embeddings.append(chunk_embedding)

                chunks.append({
                    "content": chunk,
                    "embedding": chunk_embedding,
                    "metadata": {
                        "source": file_path,
                        "type": "image",
                        "timestamp": datetime.utcnow()
                    }
                })

            # Store in MongoDB
            doc_id = self._store_document(
                title=os.path.basename(file_path),
                content=extracted_text,
                chunks=chunks,
                user_id=user_id,
                doc_type="image"
            )

            return doc_id

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    def _perform_ocr(self, image: Image.Image) -> str:
        """Perform OCR on image with preprocessing"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to numpy array
            image_np = np.array(image)

            # Preprocessing
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            binary = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )

            # Perform OCR
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(binary, config=custom_config)

            # Clean text
            cleaned_text = ' '.join(extracted_text.split())
            return cleaned_text

        except Exception as e:
            logger.error(f"Error in OCR: {str(e)}")
            return ""

    def _create_chunks(self, text: str) -> List[str]:
        """Create text chunks with overlap"""
        return self.text_splitter.split_text(text)

    def _store_document(self, title: str, content: str, chunks: List[Dict],
                        user_id: str, doc_type: str) -> str:
        """Store document and chunks in MongoDB"""
        doc_id = str(ObjectId())
        timestamp = datetime.utcnow()

        # Store document
        doc_data = {
            "_id": doc_id,
            "user_id": user_id,
            "title": title,
            "content": content,
            "type": doc_type,
            "timestamp": timestamp
        }
        self.docs_collection.insert_one(doc_data)

        # Store chunks
        chunk_data = []
        for i, chunk in enumerate(chunks):
            chunk_data.append({
                "doc_id": doc_id,
                "user_id": user_id,
                "chunk_index": i,
                "content": chunk["content"],
                "embedding": chunk["embedding"],
                "metadata": chunk["metadata"],
                "timestamp": timestamp
            })

        if chunk_data:
            self.chunks_collection.insert_many(chunk_data)

        return doc_id

    def get_document_chunks(self, user_id: str) -> List[Dict]:
        """Retrieve all chunks for a user"""
        return list(self.chunks_collection.find({"user_id": user_id}))

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Retrieve document by ID"""
        return self.docs_collection.find_one({"_id": doc_id})

    def process_query(self, query: str, user_id: str) -> ChatResponse:
        """Process a user query and generate a response"""
        try:
            # Get query embedding
            query_embedding = self.embeddings_model.embed_query(query)
            
            # Get all user's document chunks
            user_chunks = self.get_document_chunks(user_id)
            if not user_chunks:
                return ChatResponse(
                    answer="No documents found in your library to answer this query.",
                    sources=[],
                    query_type=QueryType.GENERAL.value,
                    confidence=0.0
                )

            # Calculate similarity scores
            chunk_scores = []
            for chunk in user_chunks:
                chunk_embedding = chunk["embedding"]
                similarity = self._calculate_cosine_similarity(query_embedding, chunk_embedding)
                chunk_scores.append((chunk, similarity))

            # Sort by similarity score
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Get top relevant chunks
            top_chunks = chunk_scores[:3]
            
            # Determine query type
            query_type = self._determine_query_type(query)
            
            # Generate response based on query type and relevant chunks
            response = self._generate_response(query, top_chunks, query_type)
            
            # Calculate confidence score
            confidence = max(score for _, score in top_chunks) if top_chunks else 0.0
            
            # Prepare source information
            sources = []
            for chunk, score in top_chunks:
                doc = self.get_document_by_id(chunk["doc_id"])
                if doc:
                    sources.append({
                        "doc_id": doc["_id"],
                        "title": doc["title"],
                        "relevance_score": float(score),
                        "chunk_content": chunk["content"][:200] + "..."  # Preview of chunk content
                    })

            return ChatResponse(
                answer=response,
                sources=sources,
                query_type=query_type.value,
                confidence=float(confidence)
            )

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def _calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        return dot_product / (norm1 * norm2)

    def _determine_query_type(self, query: str) -> QueryType:
        """Determine the type of query based on content analysis"""
        # Process query with spaCy
        doc = self.nlp(query.lower())
        
        # Check for study-related keywords
        study_keywords = {"explain", "analyze", "compare", "discuss", "define", "describe"}
        doc_keywords = {"document", "file", "pdf", "image", "text", "content"}
        
        # Check for keyword matches
        if any(token.text in study_keywords for token in doc):
            return QueryType.STUDY
        elif any(token.text in doc_keywords for token in doc):
            return QueryType.DOCUMENT
        else:
            return QueryType.GENERAL

    def _generate_response(self, query: str, relevant_chunks: List[tuple], query_type: QueryType) -> str:
        """Generate a response based on query type and relevant chunks"""
        chunks_content = [chunk["content"] for chunk, _ in relevant_chunks]
        
        if query_type == QueryType.STUDY:
            # For study queries, provide detailed explanations
            response = "Based on the available documents: \n\n"
            response += self._synthesize_study_response(query, chunks_content)
        
        elif query_type == QueryType.DOCUMENT:
            # For document queries, provide information about the documents
            response = self._generate_document_info_response(relevant_chunks)
        
        else:
            # For general queries, provide a direct answer
            response = self._synthesize_general_response(query, chunks_content)
        
        return response

    def _synthesize_study_response(self, query: str, chunks_content: List[str]) -> str:
        """Synthesize a detailed response for study-related queries"""
        # Combine relevant content
        combined_content = " ".join(chunks_content)
        
        # Extract key points and create a structured response
        doc = self.nlp(combined_content)
        sentences = list(doc.sents)
        
        response = ""
        for sent in sentences:
            # Add relevant sentences to the response
            if any(token.text.lower() in query.lower() for token in sent):
                response += str(sent) + " "
        
        return response.strip() or "Unable to find specific information to answer your study query."

    def _generate_document_info_response(self, relevant_chunks: List[tuple]) -> str:
        """Generate a response about document information"""
        response = "I found the following relevant documents:\n\n"
        
        for chunk, score in relevant_chunks:
            doc = self.get_document_by_id(chunk["doc_id"])
            if doc:
                response += f"- {doc['title']} (Relevance: {score:.2f})\n"
                response += f"  Content preview: {chunk['content'][:100]}...\n\n"
        
        return response

    def _synthesize_general_response(self, query: str, chunks_content: List[str]) -> str:
        """Synthesize a direct response for general queries"""
        # Combine relevant content and create a concise response
        combined_content = " ".join(chunks_content)
        doc = self.nlp(combined_content)
        
        # Extract the most relevant sentence
        most_relevant = max(doc.sents, key=lambda sent: self._sentence_relevance(sent, query))
        
        return str(most_relevant)

    def _sentence_relevance(self, sentence, query: str) -> float:
        """Calculate relevance score between a sentence and query"""
        sentence_embedding = self.embeddings_model.embed_query(str(sentence))
        query_embedding = self.embeddings_model.embed_query(query)
        
        return self._calculate_cosine_similarity(sentence_embedding, query_embedding)

    