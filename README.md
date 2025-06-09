# StudyMate: AI-Powered Learning Companion

StudyMate is a full-stack application designed to enhance the learning experience for students. It leverages AI to provide personalized study assistance, content generation, and collaborative tools. The backend is built with Python (Flask) and integrates with OpenAI and Google Gemini for various AI tasks, using MongoDB for data persistence. The frontend is a modern Next.js application using Supabase for authentication, real-time features, and additional data storage.

## Table of Contents

1.  [Core Features](#core-features)
2.  [Tech Stack](#tech-stack)
3.  [Project Structure](#project-structure)
4.  [Getting Started](#getting-started)
    *   [Prerequisites](#prerequisites)
    *   [Backend Setup (ML)](#backend-setup-ml)
    *   [Frontend Setup (Web)](#frontend-setup-web)
5.  [Key API Endpoints (Backend)](#key-api-endpoints-backend)
6.  [Key Frontend Pages/Modules](#key-frontend-pagesmodules)
7.  [Notes & Potential Future Work](#notes--potential-future-work)

## Core Features

*   **AI-Powered Content Generation:**
    *   **Quiz Generation:** Create MCQs from uploaded PDF documents or based on user's syllabus.
    *   **Flashcard Generation:** Automatically generate flashcards from text content or uploaded documents.
    *   **Course/Slide Generation:** Transform documents into a structured slideshow/course format.
    *   **Roadmap Generation:** Create personalized learning roadmaps based on user prompts and goals.
*   **Intelligent Chatbot:**
    *   Context-aware assistance using retrieved documents and user profile information.
    *   Document classification (study material, announcement, etc.).
    *   Keyword and topic extraction.
*   **User Management & Personalization:**
    *   **Authentication:** Secure user login and signup (email/password, Google OAuth via Supabase).
    *   **User Profiles:** Store user details, academic domain, year of study, and subjects.
    *   **Document Management:** Upload, store (Supabase Storage), and tag documents with subjects.
*   **Collaboration & Engagement:**
    *   **Teamspaces/Study Groups:** Create, join, and participate in real-time group chats with profanity filtering.
    *   **Interactive Quizzes & Flashcard Games:** Engage with generated content.
    *   **Quiz Evaluation:** Detailed feedback on quiz performance, including subject/chapter analysis and recommendations.
*   **Productivity & Organization:**
    *   **Personalized Dashboard:** View subjects, upcoming events/schedule (calendar).
    *   **Document Analysis:** Extract text, identify document type, and extract relevant information (e.g., syllabus changes from announcements).
*   **Experimental/Unique:**
    *   **AI Voice Calls:** (Bland.ai integration) for reminders (currently noted as potentially disabled for credit reasons).
    *   **Image Analysis:** Describe images or perform OCR using AI.

## Tech Stack

**Backend (ML - `ml/` directory):**
*   **Framework:** Python, Flask
*   **AI/ML:**
    *   OpenAI (GPT-3.5-turbo, GPT-4o-mini, Text Embeddings)
    *   Google Gemini (Gemini 2.0 Flash - for flashcards, subject summaries)
    *   Spacy (NLP, keyword extraction)
    *   Rank_BM25 (document ranking)
    *   Langchain (integrations)
*   **Database:** MongoDB (for user profiles, processed documents, roadmaps)
*   **File Processing:** PyPDF2, docx2txt
*   **Voice AI:** Bland.ai (via API)
*   **Others:** Flask-CORS, python-dotenv

**Frontend (Web - `web/` directory):**
*   **Framework:** Next.js (v15, App Router)
*   **Language:** TypeScript
*   **Styling:** Tailwind CSS, Shadcn/UI
*   **State Management/Auth:** React Context (AuthProvider), Supabase (Auth, Realtime DB, Storage)
*   **UI Components:** Radix UI (primitives for Shadcn/UI)
*   **Animation:** Framer Motion
*   **Data Fetching/Services:** Fetch API (to Flask backend and Gemini)
*   **Charts:** Recharts (likely for dashboard visualizations)
*   **Build Tool/Runtime:** Bun (indicated by `bun.lockb`)

**Databases:**
*   **MongoDB:** Primary data store for the ML backend (user profiles, extracted document content, AI-generated roadmaps).
*   **Supabase (PostgreSQL):** User authentication, user profiles (linked to auth), teamspace/group chat data, document metadata (links to Supabase Storage).

## Project Structure

```
ninet33n19-studymate/
├── README.md                 # Main project README (this file)
├── ml/                       # Python/Flask Machine Learning Backend
│   ├── app.py                # Main Flask application
│   ├── requirements.txt      # Python dependencies
│   ├── .gitignore
│   └── uitils/               # Backend utility modules
│       ├── chatbot.py
│       ├── courses.py
│       ├── extraction.py
│       ├── portfolio.py
│       ├── quiz.py           # Quiz evaluation logic
│       ├── quiznew.py        # PDF based quiz generation (seems to be a duplicate or alternative)
│       └── storage.py        # MongoDB interaction for portfolio
└── web/                      # Next.js Frontend
    ├── README.md             # Next.js specific README
    ├── package.json
    ├── next.config.ts
    ├── app/                  # Next.js App Router (pages, layouts)
    ├── components/           # React components (UI, features)
    ├── context/              # React context providers (e.g., AuthProvider)
    ├── hooks/                # Custom React hooks
    ├── lib/                  # Utility functions, Supabase provider
    ├── models/               # Mongoose schemas (seems for an alternative auth, might be legacy or unused with Supabase)
    ├── services/             # API service clients (to Flask backend)
    ├── types/                # TypeScript type definitions
    └── utils/                # General utilities, Supabase client/server setup
```

## Getting Started

### Prerequisites

*   Node.js and npm/yarn/bun
*   Python 3.8+ and pip
*   MongoDB instance running
*   Supabase project set up
*   OpenAI API Key
*   Google Gemini API Key
*   Bland.ai API Key (optional, if `/call` feature is used)

### Backend Setup (ML)

1.  **Navigate to the `ml` directory:**
    ```bash
    cd ninet33n19-studymate/ml
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    Create a `.env` file in the `ml/` directory with the following:
    ```env
    MONGO_URI="your_mongodb_connection_string"
    OPENAI_API_KEY="your_openai_api_key"
    BLANDAI_API_KEY="your_bland_ai_api_key" # Optional
    # API_KEY="your_gemini_api_key" # Used in ml/uitils/flashcards.py, ensure it's set if using that script directly
    ```
5.  **Run the Flask application:**
    ```bash
    flask run
    # or
    python app.py
    ```
    The backend will typically run on `http://127.0.0.1:5000`.

### Frontend Setup (Web)

1.  **Navigate to the `web` directory:**
    ```bash
    cd ninet33n19-studymate/web
    ```
2.  **Install dependencies:**
    ```bash
    bun install
    # or
    # npm install
    # or
    # yarn install
    ```
3.  **Set up environment variables:**
    Create a `.env.local` file in the `web/` directory with the following:
    ```env
    NEXT_PUBLIC_SUPABASE_URL="your_supabase_project_url"
    NEXT_PUBLIC_SUPABASE_ANON_KEY="your_supabase_anon_key"
    NEXT_PUBLIC_GEMINI_API_KEY="your_google_gemini_api_key" # Used for subject summaries on dashboard

    # URL for the ML backend
    NEXT_PUBLIC_API_URL="http://localhost:5000"
    ```
4.  **Run the Next.js development server:**
    ```bash
    bun dev
    # or
    # npm run dev
    # or
    # yarn dev
    ```
    The frontend will typically run on `http://localhost:3000`.

## Key API Endpoints (Backend)

The Flask backend (`ml/app.py`) exposes several endpoints, including:

*   `POST /upload`: Uploads a document and extracts text.
*   `POST /portfolio/create`: Creates a user profile.
*   `POST /portfolio/update`: Updates a user profile.
*   `POST /portfolio/roadmap`: Generates a learning roadmap for a user.
*   `POST /chatbot`: Processes a text query through the AI chatbot.
*   `GET /user`: Retrieves a user's profile.
*   `GET /user/document`: Retrieves documents uploaded by a user.
*   `POST /upload_pdf`: Uploads a PDF to generate a quiz.
*   `POST /evaluate-quiz`: Evaluates user's quiz answers.
*   `POST /quiz`: Generates a quiz based on a prompt (e.g., syllabus topics).
*   `POST /course`: Generates course slides from an uploaded document.
*   `POST /flashcards`: Generates flashcards from an uploaded document or text.
*   `POST /load-roadmaps`: Loads existing roadmaps for a user.
*   `GET /call`: Initiates an AI voice call (Bland.ai).

## Key Frontend Pages/Modules

The Next.js frontend provides interfaces for:

*   `/`: Landing page.
*   `/login`, `/signup`, `/signup/details`: Authentication and user profile completion.
*   `/dashboard`: User's main dashboard with calendar and subject overview.
*   `/documents`: Document management (upload, view, delete).
*   `/teamspace`: Create, join, and participate in study group chats.
*   `/teamspace/[id]`: Individual group chat page.
*   `/flashcards`: Interactive flashcard game.
*   `/quiz-generator`: Generate and take quizzes from uploaded documents.
*   `/quiz-results`: View quiz performance.
*   `/courses`: Generate and view course slides from documents.
*   `/ai`: Interface for interacting with the AI chatbot.
*   `/roadmap`: Generate and view personalized learning roadmaps.
*   `/admin/dashboard`: (Teacher/Admin) Dashboard for creating assignments (current implementation seems frontend-focused).

## Notes & Potential Future Work

*   **Dual Database Usage:** The project uses MongoDB for ML-backend specific data and Supabase (Postgres) for web application state, user auth, and real-time features. Clear data flow and consistency between these should be maintained.
*   **AI Model Consistency:** Different AI models (OpenAI, Gemini) are used for similar tasks (e.g., flashcard generation). Standardizing or clearly delineating their use cases could be beneficial.
*   **Error Handling:** Ensure robust error handling on both frontend and backend, especially for API calls and AI model interactions.
*   **Admin Dashboard:** The admin dashboard functionality for assignment creation appears to be primarily frontend. Backend support for managing assignments, submissions, and student performance would be a significant enhancement.
*   **Prompt Engineering:** Continuously refine AI prompts for better and more consistent output quality across features.
*   **Security:** Review security aspects, especially around file uploads, API authentication, and data validation.
*   **Testing:** The `ml/quiztest.py` and `ml/testcourse.py` suggest some level of backend testing. Comprehensive unit and integration tests for both frontend and backend would improve reliability.
*   The `ml/uitils/quiznew.py` seems to have overlapping functionality with `/upload_pdf` in `app.py` and parts of `ml/uitils/quiz.py`. This could be consolidated.
*   The Mongoose models in `web/models/` might be legacy if Supabase is the primary ORM/client for user data on the frontend side.
