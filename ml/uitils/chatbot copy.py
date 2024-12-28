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

# Retrieve documents based on query type
def retrieval(text, params):
    classification = params.get("classification")
    user_id = params.get("user_id")
    isubject = params.get("subject")
    ichapter = params.get("chapter")
    # 1. Classify the question if no classification is provided
    if not classification:
        prompt = f"Classify this query: '{text}' into either 'study-related' or 'profile-related'. Respond with only one word. Study-related queries are related to subjects, chapters, etc., while profile-related queries are related to user profiles which contain field such as information of user, their syllabus for the year, their upcoming events."
        response = generate_openai(prompt, max_tokens=5)
        classification = response.strip().lower()

    # 2. Handle study-related queries
    if classification == "study-related":
        subject_filter = params.get("subject")

        # Fetch user syllabus and use GPT to determine relevant subjects if no subject filter
        if user_id and not isubject and not ichapter:
            user_profile = users_collection.find_one({"user_id": user_id})
            # print(user_profile)
            syllabus = json.dumps(user_profile['syllabus'])

            prompt = f"From the following syllabus, determine the subjects and chapters most relevant to the query: '{text}'\n\nSyllabus:\n{syllabus}\n\nRespond with a JSON object in the format: {{'subjects': ['subject1', 'subject2'], 'chapters': ['chapter1', 'chapter2']}}"
            response = generate_openai(prompt, max_tokens=150, temperature=0.5,json_parse=True)
            try:
                # print(response)
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
        print(query)
        # Fetch documents based on the query
        docs_cursor = docs_collection.find(query)
        print (docs_cursor)
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
            doc_distances = [(doc, sum((qe - de) ** 2 for qe, de in zip(query_embedding, de))) for doc, de in zip(top_docs, doc_embeddings)]
            ranked_docs_with_embeddings = sorted(doc_distances, key=lambda x: x[1])

            # Return the top documents
            # print(ranked_docs_with_embeddings[:10])
            return {"documents": [doc[0] for doc in ranked_docs_with_embeddings[:10]],"classification":classification,"subject":subject_filter}
        else:
            return {"documents": []}

    # 3. Handle profile-related queries
    elif classification == "profile-related":
        if not user_id:
            return {"error": "User ID is required for profile-related queries"}

        user_profile = users_collection.find_one({"user_id": user_id}, {"_id": 0})
        return {"user_profile": user_profile,"classification":classification}

    return {"error": "Invalid query classification"}

# Text generation function using retrieval
def generation(query, params=None):
    if params is None:
        params = {}

    # Retrieve relevant documents
    retrieval_result = retrieval(query, params)
    if retrieval_result.get("classification") == "profile-related":
        prompt = f"Using the following user profile, answer the query:\n\n{json.dumps(retrieval_result.get('user_profile', {}), indent=4)}\n\nQuery: {query}\n\nAnswer:"
    elif retrieval_result.get("classification") == "study-related":
        documents = retrieval_result.get("documents", [])

    # Prepare context from retrieved documents
    
        if documents:
            context = "\n\n".join(documents)
            if context:
                prompt = f"Using the following study materials, answer the query:\n\n{context}\n\nQuery: {query}\n\nAnswer:"
            else:
                prompt = f"Answer the following query to the best of your ability:\n\nQuery: {query}\n\nAnswer:"
    else:
        return retrieval_result
        # prompt = f"Just return {retu}
    response = generate_openai(prompt, max_tokens=500, temperature=0.3)
    return {"generated_text": response.strip()}





def process_query(query_text, params):
    # Call the retrieval function
    retrieval_result = retrieval(query_text, params)
    documents = retrieval_result.get("documents", [])
    
    # Prepare the params string
    print(retrieval_result)
    if documents:
       
        # Attempt to extract subject and chapter information from the first document
        first_doc = documents[0]
        
        subject = retrieval_result.get("subject", [])
        chapter = retrieval_result.get("chapter", [])
        query_text = f"From the following study material, answer the query: '{query_text}'\n\n{first_doc}"
        params_info = f"Looking into study_docs in subject '{subject}' chapter '{chapter}'."
    else:
        if retrieval_result.get("classification") == "profile-related":
            params_info = "User profile information retrieved."
        else:
            query_text = f"Answer the following query: '{query_text}'"
            params_info = "No relevant documents found. Do not blindly trust the generated text."
            
    
    # Call the generation function
    generation_result = generation(query_text, params)
    
    generated_text = generation_result.get("generated_text", "")
    
    # Prepare the final result
    result = {
        "params": params_info,
        "generated_text": generated_text
    }
    
    return result

# Example usage
if __name__ == "__main__":
    # Sample query
    query_text = "Can you help me understand linked lists?"
    params = {
        "user_id": "user_1",
        "classification": None,  # Let the system classify
    }
    # result = process_query(query_text, params)
    result = retrieval(query_text, params)
    print(json.dumps(result, indent=4))
