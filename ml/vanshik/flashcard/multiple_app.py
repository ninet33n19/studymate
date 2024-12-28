import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import json
# Import the SimpleFlashcardGenerator
from flashcards import SimpleFlashcardGenerator
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()

# Initialize the generator with your API key
API_KEY = os.getenv("API KEY")  # Replace with your actual API key
generator = SimpleFlashcardGenerator(API_KEY)

class FolderRequest(BaseModel):
    folder_path: str

@app.post("/generate-flashcards")
async def generate_flashcards(request: FolderRequest):
    try:
        # Process the PDFs and generate flashcards
        result = generator.process_pdfs(request.folder_path)
        
        # Save results
        with open("flashcards.json", "w") as f:
            json.dump(result, f, indent=2)
        
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_server():
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    run_server()