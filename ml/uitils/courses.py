import os
import json
import mimetypes
from .extraction import extract_text_from_file
from .chatbot import generate_openai

# Function to split text into chunks
def split_text_into_chunks(text, chunk_size=1000):
    words = text.split()
    return [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def generate_course(file, output_path=None, chunk_size=2000):
    """
    Generate course content based on the input file.

    Args:
        file: The file object sent from a Flask endpoint or similar.
        output_path: (Optional) Path to save the generated JSON file.
        chunk_size: Number of characters per chunk for processing.

    Returns:
        dict: The generated course content as JSON.
    """
    try:
        # Detect file type (mimetype)
        mimetype, _ = mimetypes.guess_type(file.filename)

        # Extract text from the file
        text = extract_text_from_file(file, mimetype)

        # Split text into chunks
        chunks = split_text_into_chunks(text, chunk_size=chunk_size)

        # Define the system prompt
        system_prompt = (
            "You are a teacher generating educational slides. For each chunk of input text, "
            "return a JSON array with the key 'slides'. The content should be aesthetically pleasing "
            "and in markdown format to make it easier for beginners to understand."
        )

        # Generate slides for each chunk
        slides = []
        for chunk in chunks:
            response = generate_openai(f"{system_prompt}. The current context is {chunk}", json_parse=True)

            # Handle potential null response
            if response is None:
                raise Exception("Received null response from OpenAI API")

            # Handle potential missing slides key
            if not isinstance(response, dict):
                raise Exception(f"Expected dict response, got {type(response)}")

            if 'slides' not in response:
                raise Exception("Response missing required 'slides' key")

            # Assuming GPT returns a JSON object with a 'slides' key
            slides.extend(response['slides'])

        # Merge slides into a single JSON object
        final_output = {"slides": slides}

        # Optionally save to a JSON file
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, ensure_ascii=False, indent=4)

        # Return the generated content as JSON
        return final_output

    except Exception as e:
        raise Exception(f"An error occurred while generating the course: {str(e)}")
