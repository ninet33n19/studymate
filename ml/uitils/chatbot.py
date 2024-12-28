import os
import json
import dotenv
import requests
from pymongo import MongoClient
from rank_bm25 import BM25Okapi
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import openai
from io import BufferedReader
import spacy

# Load environment variables
dotenv.load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Initialize OpenAI API
openai.api_key = openai_api_key
chatopenai = ChatOpenAI(api_key=openai_api_key, model='gpt-4o-mini')

# MongoDB setup
client = MongoClient(mongo_uri)
db = client['RGIT_DB']
users_collection = db['users']
docs_collection = db['metadata']

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# BM25 ranking function
def get_bm25_ranking(query, docs):
    tokenized_corpus = [nlp(doc["document_content"]["extracted_text"]) for doc in docs]
    bm25 = BM25Okapi([doc.text.split() for doc in tokenized_corpus])
    
    # Tokenize the query using spaCy NLP
    query_doc = nlp(query)
    query_keywords = query_doc.text.split()
    
    # Get BM25 scores for the query
    doc_scores = bm25.get_scores(query_keywords)
    return doc_scores
def generate_openai(prompt,max_tokens=2000,temperature=0.3,model='gpt-4o-mini',json_parse=False):
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if json_parse:
        result = response.choices[0].message.content.replace("```json","").replace("```","")
        result = json.loads(result)
    else :
        result = response.choices[0].message.content
    return result

def retrieval(text, params):
    classification = params.get("classification")
    user_id = params.get("user_id")
    isubject = params.get("subject")
    ichapter = params.get("chapter")
    
    # 1. Classify the question if no classification is provided
    if not classification:
        prompt = (
            f"Classify this query: '{text}' into either 'study-related' or 'profile-related'. "
            "Respond with only one word. Study-related queries are related to subjects, chapters, etc., "
            "while profile-related queries are related to user profiles which contain fields such as "
            "information of user, their syllabus for the year, their upcoming events."
        )
        response = generate_openai(prompt, max_tokens=15)
        classification = response.strip().lower()

    # 2. Handle study-related queries
    if classification == "study-related":
        subject_filter = params.get("subject")

        # Fetch user syllabus and use GPT to determine relevant subjects if no subject filter
        if user_id and not isubject and not ichapter:
            user_profile = users_collection.find_one({"user_id": user_id})
            syllabus = json.dumps(user_profile['syllabus'])

            prompt = (
                f"From the following syllabus, determine the subjects and chapters most relevant to the query: '{text}'\n\n"
                f"Syllabus:\n{syllabus}\n\n"
                "Respond with a JSON object in the format: {'subjects': ['subject1', 'subject2'], 'chapters': ['chapter1', 'chapter2']}"
            )
            response = generate_openai(prompt, max_tokens=3000, temperature=0.2, json_parse=True)
            try:
                subject_info = response
                subject_filter = subject_info.get('subjects', [])
                chapter_filter = subject_info.get('chapters', [])
                if isubject:
                    subject_filter = [isubject]
                if ichapter:
                    chapter_filter = [ichapter]
            except json.JSONDecodeError:
                subject_filter = []
                chapter_filter = []
        else:
            chapter_filter = []

        # Build the query for MongoDB
        query = {}
        if subject_filter:
            query["classification.subject"] = {"$in": subject_filter}
        # if chapter_filter:
        #     query["classification.chapter_name"] = {"$in": chapter_filter}

        # Fetch documents based on the query
        docs_cursor = docs_collection.find(query)
        docs = [doc for doc in docs_cursor]

        # Use BM25 for retrieval
        if docs:
            bm25_scores = get_bm25_ranking(text, docs)
            ranked_docs = sorted(zip(bm25_scores, docs), key=lambda x: x[0], reverse=True)

            # Use embeddings to rerank the top 10 documents (optional, for more refinement)
            top_docs = [doc[1]["document_content"]["extracted_text"] for doc in ranked_docs[:10]]
            embeddings = OpenAIEmbeddings(api_key=openai_api_key)
            query_embedding = embeddings.embed_query(text)
            doc_embeddings = embeddings.embed_documents(top_docs)
            doc_distances = [
                (doc, sum((qe - de) ** 2 for qe, de in zip(query_embedding, de)))
                for doc, de in zip(top_docs, doc_embeddings)
            ]
            ranked_docs_with_embeddings = sorted(doc_distances, key=lambda x: x[1])

            # Return the top documents
            return {
                "documents": [doc[0] for doc in ranked_docs_with_embeddings[:10]],
                "classification": classification,
                "subject": subject_filter,
                "chapter": chapter_filter,
            }
        else:
            return {"documents": [], "classification": classification}

    # 3. Handle profile-related queries
    elif classification == "profile-related":
        if not user_id:
            return {"error": "User ID is required for profile-related queries"}
        user_profile = users_collection.find_one({"user_id": user_id}, {"_id": 0})
        return {"user_profile": user_profile, "classification": classification}

    return {"error": "Invalid query classification"}

# Process the query and generate the response
def process_query(query_text, params):
    # Call the retrieval function once
    retrieval_result = retrieval(query_text, params)

    # Prepare the params string
    classification = retrieval_result.get("classification")
    if classification == "study-related":
        documents = retrieval_result.get("documents", [])
        subject = retrieval_result.get("subject", [])
        chapter = retrieval_result.get("chapter", [])
        if documents:
            context = "\n\n".join(documents)
            prompt = (
                f"Using the following study materials, answer the query:\n\n{context}\n\n"
                f"Query: {query_text}\n\nAnswer:"
            )
            params_info = f"Looking into study_docs in subject '{subject}' chapter '{chapter}'."
        else:
            prompt = (
                f"Answer the following query to the best of your ability:\n\n"
                f"Query: {query_text}\n\nAnswer:"
            )
            params_info = "No relevant documents found. Do not blindly trust the generated text."
    elif classification == "profile-related":
        user_profile = retrieval_result.get('user_profile', {})
        prompt = (
            f"Using the following user profile, answer the query:\n\n{json.dumps(user_profile, indent=4)}\n\n"
            f"Query: {query_text}\n\nAnswer:"
        )
        params_info = "User profile information retrieved."
    else:
        prompt = (
            f"Answer the following query to the best of your ability:\n\n"
            f"Query: {query_text}\n\nAnswer:"
        )
        params_info = "No relevant information found."

    # Call the OpenAI API to generate the answer
    generated_text = generate_openai(f"{prompt}. Only reply in plaintext and not markdown.", max_tokens=5000, temperature=0.3).strip()

    # Prepare the final result
    result = {
        "params": params_info,
        "generated_text": generated_text
    }
    return result

def generate_quiz(portion,user_id,num_questions=5):

    
    #load the user profile
    user_profile = users_collection.find_one({"user_id": user_id})
    #choose syllabus
    
    
    #filter the portion according to the user syllabus for this test
    allowed_portion = []
    if len(portion)!=0:
        for i in range(len(user_profile['syllabus'])):
            for j in range(len(portion)):
                if user_profile['syllabus'][i]['subject'] == portion[j]:
                    allowed_portion.append(user_profile['syllabus'][i])
    else:
        allowed_portion = user_profile['syllabus']
    
    print(allowed_portion)
    
        
    
    
    
    QUIZ_PROMPT = f"""
    You are a mcq quiz generator. From the following syllabus, generate a quiz with {num_questions} questions based on the user's syllabus.
    The syllabus is: {allowed_portion}
    Return a JSON object with the following format:
    {{
        "questions": [
            {{
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "answer": "Paris",
                "subject":"Geography",
                "chapter":"Europe",
                "difficulty":"easy",
                "marks":1,
                "hint":"The Eiffel Tower is located in this city.",
                "question_number":1
            }},
            {{
                "question": "What is 2+2?",
                "options": ["3", "4", "5", "6"],
                "answer": "4",
                "subject":"Math",
                "chapter":"Arithmetic",
                "difficulty":"easy",
                "marks":1,
                "hint":"The answer is 4.",
                "question_number":2
                
            }}
        ]
    }}
    """
    response = generate_openai(QUIZ_PROMPT, max_tokens=2000, temperature=0.3, json_parse=True)
    
    
    return response

# Example usage
if __name__ == "__main__":
    # Sample query
    query_text = "Can you help me understand linked lists?"
    params = {
        "user_id": "user_1",
        "classification": None,  # Let the system classify
    }
    result = process_query(query_text, params)
    print(json.dumps(result, indent=4))
    
    
    
    
def check_up_call(student_name):
    # Headers
    headers = {
        'Authorization': os.getenv("BLANDAI_API_KEY")
    }

    # Data
    data = {
        'phone_number': '+919167606652',
        'task': f"You are a study assistant. Remind the student named {student_name} to complete their assignments today.",
        'voice_id': 1,
        'reduce_latency': True,
        'request_data': {},
        'voice_settings': {
            'speed': 1
        },
        'interruption_threshold': 0,
        'start_time': None,
        'transfer_phone_number': None,
        'answered_by_enabled': False,
        'from': None,
        'first_sentence': None,
        'record': True,
        'max_duration': 2,
        'model': 'enhanced',
        'language': 'ENG'
    }

    # API request 
    response = requests.post('https://api.bland.ai/call', json=data, headers=headers)
    print(response.text)  # Print response for debugging purposes
    return response.text


