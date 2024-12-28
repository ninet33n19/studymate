import os
os.environ['GRPC_DNS_RESOLVER'] = 'native'
os.environ['PROTOCOL'] = 'IPv4'
from typing import List, Dict, Optional
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
from langchain.prompts import PromptTemplate
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import pytesseract
from PIL import Image
import numpy as np
import cv2
from rank_bm25 import BM25Okapi
import spacy
import json
from dataclasses import dataclass
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load spaCy model for text processing
nlp = spacy.load("en_core_web_sm")

class QueryType(Enum):
    STUDY = "study"
    GENERAL = "general"
    DOCUMENT = "document"
    PROFILE = "profile"

@dataclass
class UserProfile:
    user_id: str
    name: str
    course: str
    year: int
    semester: int
    subjects: List[str]
    syllabus: Dict

@dataclass
class QueryContext:
    query_type: QueryType
    subject: Optional[str] = None
    chapter: Optional[str] = None
    user_profile: Optional[UserProfile] = None

class EnhancedRAGChatbot:
    def __init__(self, document_path: str, google_api_key: str, user_profile: Optional[UserProfile] = None):
        self.document_path = document_path
        self.pdf_path = document_path
        self.document_title = ""
        self.document_abstract = ""
        self.user_profile = user_profile
        
        # Initialize memory with metadata
        self.memory = ConversationBufferMemory(
            return_messages=True,
            output_key='answer',
            memory_key='chat_history',
            input_key='question'
        )
        
        # Initialize Gemini and other components
        try:
            os.environ["GOOGLE_API_KEY"] = google_api_key
            genai.configure(api_key=google_api_key)
            self.ocr_enabled = True
            self.llm = self._initialize_gemini()
        except Exception as e:
            print(f"Warning: OCR initialization failed: {str(e)}")
            self.ocr_enabled = False
            raise Exception(f"Failed to initialize Gemini: {str(e)}")
        
        self.embeddings = self._initialize_embeddings()
        self.vector_store = None
        self.qa_chain = None
        self.bm25_index = None
        
        # Enhanced text splitting with better chunk handling
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=150,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
    def _extract_title(self, first_page_content: str) -> str:
        """Extract title from the first page"""
        try:
            lines = first_page_content.split('\n')
            for line in lines[:5]:
                cleaned_line = line.strip()
                if cleaned_line and not any(word in cleaned_line.lower() 
                    for word in ['abstract', 'contents', 'chapter', 'page']):
                    return cleaned_line
            return "Untitled Document"
        except Exception as e:
            print(f"Error extracting title: {str(e)}")
            return "Untitled Document"

    def _extract_abstract(self, first_page_content: str) -> str:
        """Extract abstract from the first page"""
        try:
            content = first_page_content.lower()
            abstract_start = content.find('abstract')
            if abstract_start != -1:
                possible_ends = [
                    content.find('introduction', abstract_start),
                    content.find('\n\n', abstract_start),
                    content.find('keywords', abstract_start)
                ]
                valid_ends = [end for end in possible_ends if end != -1]
                if valid_ends:
                    abstract_end = min(valid_ends)
                    return first_page_content[abstract_start:abstract_end].strip()
            return ""
        except Exception as e:
            print(f"Error extracting abstract: {str(e)}")
            return ""

    def _process_ocr_text(self, text: str) -> str:
        """Clean and process OCR text"""
        text = ' '.join(text.split())
        text = text.replace('|', 'I').replace('[', '').replace(']', '')
        sentences = text.split('.')
        cleaned_sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        return '. '.join(cleaned_sentences)

    def _process_image_document(self, image_path: str) -> List[Document]:
        """Process image and convert to document format"""
        try:
            extracted_text = self.process_image(image_path)
            if extracted_text:
                return [Document(
                    page_content=extracted_text,
                    metadata={
                        "source": image_path,
                        "type": "image",
                        "page": 1,
                        "priority": "high",
                        "section": "image_content"
                    }
                )]
            return []
        except Exception as e:
            print(f"Error processing image document: {str(e)}")
            return []

    def _process_documents_with_emphasis(self, documents: List[Document]) -> List[Document]:
        """Process documents with emphasis on important sections"""
        processed_chunks = []
        important_keywords = {
            'abstract': 'highest',
            'introduction': 'high',
            'methodology': 'high',
            'results': 'high',
            'discussion': 'high',
            'conclusion': 'high',
            'findings': 'high',
            'research objectives': 'high',
            'experimental': 'medium',
            'analysis': 'medium',
            'literature review': 'medium',
            'background': 'medium'
        }

        def determine_section_and_priority(text: str) -> tuple:
            text_lower = text.lower()
            section_type = "general"
            priority = "normal"
            
            for keyword, importance in important_keywords.items():
                if keyword in text_lower:
                    if text_lower.strip().startswith(keyword):
                        section_type = keyword
                        priority = importance
                        break
                    else:
                        priority = importance
            return section_type, priority

        if documents:
            first_page = documents[0]
            first_page_chunks = self.text_splitter.split_text(first_page.page_content)
            
            for i, chunk in enumerate(first_page_chunks):
                section_type, priority = determine_section_and_priority(chunk)
                
                if i == 0:
                    priority = "highest"
                    section_type = "title_and_abstract"
                
                processed_chunks.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "page": 1,
                            "source": self.document_path,
                            "section": section_type,
                            "priority": priority,
                            "chunk_order": i
                        }
                    )
                )

        for doc_index, doc in enumerate(documents[1:], start=1):
            page_number = doc.metadata.get("page", doc_index + 1)
            chunks = self.text_splitter.split_text(doc.page_content)
            
            for chunk_index, chunk in enumerate(chunks):
                section_type, base_priority = determine_section_and_priority(chunk)
                
                metadata = {
                    "page": page_number,
                    "source": self.document_path,
                    "section": section_type,
                    "priority": base_priority,
                    "chunk_order": chunk_index
                }
                
                if section_type in ['abstract', 'introduction', 'conclusion']:
                    sub_chunks = self.text_splitter.split_text(chunk)
                    for sub_index, sub_chunk in enumerate(sub_chunks):
                        processed_chunks.append(
                            Document(
                                page_content=sub_chunk,
                                metadata={
                                    **metadata,
                                    "sub_chunk": sub_index,
                                    "is_sub_chunk": True
                                }
                            )
                        )
                else:
                    processed_chunks.append(
                        Document(
                            page_content=chunk,
                            metadata=metadata
                        )
                    )

        for i, chunk in enumerate(processed_chunks):
            chunk.metadata["total_chunks"] = len(processed_chunks)
            chunk.metadata["position_ratio"] = i / len(processed_chunks)
            chunk.metadata["context_importance"] = "high" if chunk.metadata["position_ratio"] < 0.1 or chunk.metadata["position_ratio"] > 0.9 else "normal"

        return processed_chunks

    def _format_response(self, response: str) -> str:
        """Format the response for better readability"""
        response = response.strip()
        if ":" in response:
            formatted = ""
            for line in response.split("\n"):
                if ":" in line:
                    formatted += f"\n• {line.strip()}"
                else:
                    formatted += f"\n  {line.strip()}"
            return formatted.strip()
        return response
    def _initialize_gemini(self):
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            temperature=0.3,
            convert_system_message_to_human=False,
            top_k=40,
            top_p=0.9,
            generation_config=generation_config
        )

    def _initialize_embeddings(self):
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )

    def _create_dual_ranking_prompt(self):
        template = """
        You are an intelligent assistant with access to both document content and user profile information.
        
        Current User Context:
        {user_context}
        
        Document Context:
        {context}
        
        When analyzing questions:
        1. For study-related queries:
           - Consider the user's current subjects and syllabus
           - Provide accurate information from the documents
           - Reference specific sections and pages
        
        2. For document-specific queries:
           - Focus on the document's content and structure
           - Highlight key findings and methodologies
           - Maintain academic accuracy
        
        3. For general queries:
           - Combine document knowledge with general understanding
           - Provide comprehensive but focused answers
           - Cite sources when applicable
        
        Current Question: {question}
        
        Remember to:
        1. Be specific and accurate
        2. Use appropriate technical terms
        3. Provide relevant examples when helpful
        4. Clearly indicate information sources
        
        Answer:
        """
        return PromptTemplate(
            template=template,
            input_variables=["context", "question", "user_context"]
        )

    def _classify_query(self, query: str) -> QueryType:
        """Classify the query type using Gemini"""
        prompt = f"""
        Classify this query into one of these categories: STUDY, GENERAL, DOCUMENT, PROFILE
        Query: {query}
        Consider:
        - STUDY: Questions about specific subjects, topics, or academic content
        - DOCUMENT: Questions about the current document's content or structure
        - PROFILE: Questions about user profile, courses, or personal information
        - GENERAL: Other general questions
        
        Return only the category name.
        """
        
        response = self.llm.invoke(prompt).content.strip().upper()
        return QueryType[response]
    def _create_bm25_index(self, documents: List[Document]):
        """Create BM25 index for document ranking"""
        tokenized_docs = [
            [token.text.lower() for token in nlp(doc.page_content)]
            for doc in documents
        ]
        self.bm25_index = BM25Okapi(tokenized_docs)
        return tokenized_docs

    def _hybrid_ranking(self, query: str, documents: List[Document], top_k: int = 5):
        """Combine BM25 and embedding-based ranking"""
        # BM25 ranking
        query_tokens = [token.text.lower() for token in nlp(query)]
        bm25_scores = self.bm25_index.get_scores(query_tokens)
        
        # Embedding ranking
        query_embedding = self.embeddings.embed_query(query)
        doc_embeddings = [
            self.embeddings.embed_query(doc.page_content)
            for doc in documents
        ]
        
        # Calculate similarity scores
        similarity_scores = [
            np.dot(query_embedding, doc_embedding) / 
            (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding))
            for doc_embedding in doc_embeddings
        ]
        
        # Combine scores (weighted average)
        combined_scores = [
            0.3 * bm25 + 0.7 * sim
            for bm25, sim in zip(bm25_scores, similarity_scores)
        ]
        
        # Get top documents
        ranked_indices = np.argsort(combined_scores)[-top_k:][::-1]
        return [documents[i] for i in ranked_indices]

    def process_image(self, image_path: str) -> str:
        """Enhanced image processing with better OCR"""
        try:
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhanced preprocessing
            image_np = np.array(image)
            
            # Apply multiple preprocessing techniques
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Perform OCR with improved settings
            custom_config = r'--oem 3 --psm 6 -l eng'
            extracted_text = pytesseract.image_to_string(binary, config=custom_config)
            
            return self._process_ocr_text(extracted_text)
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return ""
    def load_and_process_document(self, file_path: str):
        """Enhanced document processing with hybrid ranking and multimodal support"""
        self.document_path = file_path
        file_extension = os.path.splitext(file_path)[1].lower()
        
        try:
            documents = []
            
            # Handle different file types
            if file_extension == '.pdf':
                print("Processing PDF document...")
                documents = self._process_pdf()
            elif file_extension in ['.png', '.jpg', '.jpeg']:
                print("Processing image document...")
                # Process image and create document
                extracted_text = self.process_image(file_path)
                if extracted_text:
                    documents = [Document(
                        page_content=extracted_text,
                        metadata={
                            "source": file_path,
                            "type": "image",
                            "page": 1,
                            "priority": "high",
                            "section": "image_content"
                        }
                    )]
            else:
                return False, f"Unsupported file format: {file_extension}"
            
            if not documents:
                return False, "No content extracted from document"
            
            print(f"Extracted content length: {sum(len(doc.page_content) for doc in documents)} characters")
            
            # Create chunks for processing
            chunks = []
            for doc in documents:
                doc_chunks = self.text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(doc_chunks):
                    chunks.append(Document(
                        page_content=chunk,
                        metadata={
                            **doc.metadata,
                            "chunk_index": i,
                            "total_chunks": len(doc_chunks)
                        }
                    ))
            
            print(f"Created {len(chunks)} chunks for processing")
            
            # Create indices for hybrid ranking
            tokenized_docs = self._create_bm25_index(chunks)
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            # Initialize enhanced QA chain
            self.qa_chain = self._create_qa_chain()
            
            return True, f"Successfully processed {os.path.basename(file_path)}"
            
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            print(error_msg)
            return False, error_msg

    def process_image(self, image_path: str) -> str:
        """Enhanced image processing with OCR"""
        try:
            # Read image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array for preprocessing
            image_np = np.array(image)
            
            # Enhanced preprocessing pipeline
            # 1. Convert to grayscale
            gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            
            # 2. Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 3. Apply adaptive thresholding
            binary = cv2.adaptiveThreshold(
                denoised, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            # 4. Apply dilation to connect text components
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
            dilated = cv2.dilate(binary, kernel, iterations=1)
            
            # 5. Perform OCR with improved settings
            custom_config = r'--oem 3 --psm 6 -l eng+equ'  # Added equ for equation support
            extracted_text = pytesseract.image_to_string(dilated, config=custom_config)
            
            # Process and clean the extracted text
            cleaned_text = self._process_ocr_text(extracted_text)
            
            if not cleaned_text:
                print("Warning: No text extracted from image")
                return "No readable text found in the image."
            
            print(f"Successfully extracted {len(cleaned_text)} characters from image")
            return cleaned_text
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return ""

    def _process_pdf(self):
        """Process PDF with enhanced chunking and structure analysis"""
        loader = PyPDFLoader(self.document_path)
        documents = loader.load()
        
        # Extract metadata
        if documents:
            first_page = documents[0].page_content
            self.document_title = self._extract_title(first_page)
            self.document_abstract = self._extract_abstract(first_page)
        
        # Process with emphasis on structure
        return self._process_documents_with_emphasis(documents)

    def _create_qa_chain(self):
        """Create enhanced QA chain with hybrid retrieval"""
        return ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 5,
                    "fetch_k": 8,
                    "lambda_mult": 0.7
                }
            ),
            memory=self.memory,
            return_source_documents=True,
            verbose=False,
            combine_docs_chain_kwargs={
                "prompt": self._create_dual_ranking_prompt()
            }
        )
    def chat(self, question: str) -> Dict:
        """Enhanced chat function with query classification and context awareness"""
        try:
            if not self.qa_chain:
                raise ValueError("Please load document first")
            
            # Classify query
            query_type = self._classify_query(question)
            
            # Prepare context based on query type
            context = self._prepare_context(question, query_type)
            
            # Get response using hybrid ranking
            result = self.qa_chain.invoke({
                "question": question,
                "chat_history": self.memory.chat_memory.messages,
                "user_context": context
            })
            
            # Format and enhance response
            response = self._enhance_response(result, query_type)
            
            return response
            
        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            print(error_msg)
            return {
                "answer": error_msg,
                "sources": [],
                "query_type": str(query_type) if 'query_type' in locals() else "unknown",
                "document": os.path.basename(self.document_path)
            }

    def _prepare_context(self, question: str, query_type: QueryType) -> str:
        """Prepare context based on query type and user profile"""
        context = ""
        
        if query_type == QueryType.STUDY and self.user_profile:
            context += f"\nUser is studying {self.user_profile.course} "
            context += f"Year {self.user_profile.year}, Semester {self.user_profile.semester}\n"
            context += f"Current subjects: {', '.join(self.user_profile.subjects)}\n"
        
        elif query_type == QueryType.DOCUMENT:
            context += f"\nDocument Title: {self.document_title}\n"
            if self.document_abstract:
                context += f"Abstract: {self.document_abstract}\n"
        
        return context

    def _enhance_response(self, result: Dict, query_type: QueryType) -> Dict:
        """Enhance response with additional context and metadata"""
        formatted_answer = self._format_response(result['answer'])
        
        # Get sources with metadata
        sources = []
        for doc in result.get('source_documents', []):
            if doc.metadata.get('priority') == 'high':
                source = {
                    "page": doc.metadata.get('page', 'Unknown'),
                    "section": doc.metadata.get('section', 'Unknown'),
                    "priority": doc.metadata.get('priority', 'normal')
                }
                sources.append(source)
        
        return {
            "answer": formatted_answer,
            "sources": sources,
            "query_type": str(query_type),
            "document": os.path.basename(self.document_path)
        }
def main():
    # Configuration
    DOCUMENT_PATH = "your-image-or-document-path"  # Your image path
    GOOGLE_API_KEY = os.getenv("API_KEY")  # Your  API key
    
    # Sample user profile
    user_profile = UserProfile(
        user_id="user1",
        name="John Doe",
        course="Computer Science",
        year=2,
        semester=3,
        subjects=["Data Structures", "Algorithms", "Database Systems"],
        syllabus={
            "Data Structures": ["Arrays", "Linked Lists", "Trees"],
            "Algorithms": ["Sorting", "Searching", "Graph Algorithms"],
            "Database Systems": ["SQL", "Normalization", "Transactions"]
        }
    )
    
    try:
        # Initialize chatbot
        print("Initializing enhanced chatbot...")
        chatbot = EnhancedRAGChatbot(DOCUMENT_PATH, GOOGLE_API_KEY, user_profile)
        
        # Process initial document
        print(f"Processing document: {os.path.basename(DOCUMENT_PATH)}...")
        success, message = chatbot.load_and_process_document(DOCUMENT_PATH)
        if not success:
            print(f"Failed to process document: {message}")
            return
        
        print("\nEnhanced chatbot is ready! You can start asking questions.")
        print("Commands:")
        print("- Type 'quit' to exit")
        print("- Type 'image' to process a new image")
        print("- Type 'pdf' to process a new PDF")
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() == 'quit':
                break
            
            if user_input.lower() in ['image', 'pdf']:
                file_path = input("Enter file path: ").strip()
                if os.path.exists(file_path):
                    print(f"Processing new {user_input}...")
                    success, message = chatbot.load_and_process_document(file_path)
                    if success:
                        print(f"Successfully processed {os.path.basename(file_path)}")
                    else:
                        print(f"Failed to process file: {message}")
                    continue
                else:
                    print("Invalid file path")
                    continue
            
            response = chatbot.chat(user_input)
            
            print("\n" + "="*50)
            print(f"\nQuery Type: {response['query_type']}")
            print("\nAnswer:")
            print(response['answer'])
            
            if response['sources']:
                print("\nSources:")
                for source in response['sources']:
                    if source.get('type') == 'image':
                        print(f"- From image: {os.path.basename(source['source'])}")
                    else:
                        print(f"- Page {source['page']}, Section: {source['section']}")
            
            print("="*50 + "\n")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
    