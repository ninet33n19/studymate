const API_BASE_URL = "http://localhost:5000"; // Replace with your backend URL

export interface QuizQuestion {
  question_number: number;
  question: string;
  options: string[];
  answer: string;
  subject: string;
  chapter: string;
  marks: number;
}

export interface QuizResponse {
  response: {
    questions: QuizQuestion[];
  };
}

export interface QuizResult {
  user_id: string;
  total_questions: number;
  correct_answers: number;
  total_marks: number;
  obtained_marks: number;
  overall_percentage: number;
  subject_analysis: Record<string, any>;
  chapter_analysis: Record<string, any>;
  recommendations: string[];
  details: any[];
}

export const quizApi = {
  generateQuiz: async (
    prompt: string,
    userId: string,
    numQuestions: number = 5,
  ): Promise<QuizResponse> => {
    const response = await fetch(`${API_BASE_URL}/quiz`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        prompt,
        user_id: userId,
        num_questions: numQuestions,
      }),
    });
    return response.json();
  },

  submitQuizAnswers: async (
    quizResponse: QuizResponse,
    userAnswers: Record<number, string>,
    userId: string,
  ): Promise<QuizResult> => {
    const response = await fetch(`${API_BASE_URL}/evaluate-quiz`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        quiz_response: quizResponse,
        user_answers: userAnswers,
        user_id: userId,
      }),
    });
    return response.json();
  },
};
