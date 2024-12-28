import os
from pathlib import Path
import PyPDF2
import google.generativeai as genai
import json
import time
from typing import List, Dict, Any
import textwrap

class EnhancedFlashcardGenerator:
    def __init__(self, api_key: str):
        """Initialize the flashcard generator with API key and configuration."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.chunk_size = 3000
        self.cards_per_chunk = 5

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF with improved formatting."""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = []
                for page in reader.pages:
                    # Clean and normalize text
                    page_text = page.extract_text()
                    page_text = ' '.join(page_text.split())  # Normalize whitespace
                    text.append(page_text)
                return '\n\n'.join(text)
        except Exception as e:
            print(f"Error reading PDF {pdf_path}: {e}")
            return ""

    def chunk_content(self, content: str) -> List[str]:
        """Split content into manageable chunks while preserving context."""
        words = content.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > self.chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        return chunks

    def generate_improved_prompt(self, content: str, source: str, chunk_index: int) -> str:
        """Generate an enhanced prompt for better flashcard creation."""
        return textwrap.dedent(f"""
            Create educational flashcards from this content chunk {chunk_index + 1}.
            Focus on key concepts, definitions, relationships, and practical applications.
            
            Content: {content}
            
            Generate {self.cards_per_chunk} high-quality flashcards that:
            1. Cover different difficulty levels (basic to advanced)
            2. Include both factual and conceptual questions
            3. Encourage critical thinking
            4. Are clear and unambiguous
            
            Format each flashcard as a JSON object with these fields:
            {{
                "question": "Clear, specific question",
                "answer": "Concise but complete answer",
                "topic": "Specific topic or concept",
                "difficulty": "basic|intermediate|advanced",
                "type": "factual|conceptual|application",
                "source": "{source}",
                "chunk_index": {chunk_index}
            }}
            
            Return the flashcards as a JSON array.
            """)

    def generate_flashcards(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Generate comprehensive flashcards from content chunks."""
        all_flashcards = []
        content_chunks = self.chunk_content(content)
        
        for i, chunk in enumerate(content_chunks):
            try:
                prompt = self.generate_improved_prompt(chunk, source, i)
                response = self.model.generate_content(prompt)
                
                if response and hasattr(response, 'text'):
                    clean_text = response.text.strip()
                    # Remove any markdown code block indicators
                    clean_text = clean_text.replace('```json', '').replace('```', '').strip()
                    
                    try:
                        chunk_flashcards = json.loads(clean_text)
                        if isinstance(chunk_flashcards, list):
                            all_flashcards.extend(chunk_flashcards)
                        else:
                            print(f"Invalid flashcard format in chunk {i}")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error in chunk {i}: {e}")
                
                # Add delay between API calls
                time.sleep(2)
            
            except Exception as e:
                print(f"Error processing chunk {i} from {source}: {e}")
                continue
        
        return all_flashcards

    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process a single PDF and generate comprehensive flashcards."""
        pdf_file = Path(pdf_path)
        result = {
            "file_name": pdf_file.name,
            "status": "success",
            "flashcards": [],
            "metadata": {
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_chunks": 0,
                "total_cards": 0
            }
        }

        if not pdf_file.exists() or pdf_file.suffix.lower() != '.pdf':
            result["status"] = "error"
            result["error"] = f"{pdf_path} is not a valid PDF file"
            return result

        content = self.extract_text_from_pdf(pdf_path)
        if not content:
            result["status"] = "error"
            result["error"] = f"No text could be extracted from {pdf_path}"
            return result

        # Generate and validate flashcards
        flashcards = self.generate_flashcards(content, pdf_file.name)
        
        if flashcards:
            result["flashcards"] = flashcards
            result["metadata"]["total_chunks"] = len(self.chunk_content(content))
            result["metadata"]["total_cards"] = len(flashcards)
        else:
            result["status"] = "warning"
            result["message"] = "No flashcards generated. Please check the content or try again."

        return result

    def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """Process all PDFs in a directory."""
        dir_path = Path(directory_path)
        results = {
            "summary": {
                "total_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "total_flashcards": 0
            },
            "files": []
        }

        if not dir_path.exists() or not dir_path.is_dir():
            results["error"] = f"{directory_path} is not a valid directory"
            return results

        for pdf_file in dir_path.glob('*.pdf'):
            result = self.process_pdf(str(pdf_file))
            results["files"].append(result)
            
            results["summary"]["total_files"] += 1
            if result["status"] == "success":
                results["summary"]["successful_files"] += 1
                results["summary"]["total_flashcards"] += len(result["flashcards"])
            else:
                results["summary"]["failed_files"] += 1

        return results