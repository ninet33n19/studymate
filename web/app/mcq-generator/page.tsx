"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";
import { quizApi, QuizQuestion, QuizResponse } from "@/services/quiz";

const NoQuestionsMessage = () => {
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8 text-center">
        <div className="space-y-6">
          {/* You can add an icon here */}
          <div className="text-gray-400 mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-20 w-20 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          <h2 className="text-2xl font-bold text-gray-700">
            No Questions Available
          </h2>

          <p className="text-gray-500">
            We couldn't load any questions at the moment. This might be due to:
          </p>

          <ul className="text-gray-500 text-sm list-disc list-inside">
            <li>Connection issues</li>
            <li>Server maintenance</li>
            <li>Invalid quiz parameters</li>
          </ul>

          <Button onClick={() => window.location.reload()} className="mt-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Try Again
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default function MCQGenerator() {
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [userAnswers, setUserAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Generate quiz when component mounts
    const generateQuiz = async () => {
      try {
        const userId = "user_50"; // Replace with actual user ID
        const prompt = "Generate a quiz about programming"; // Replace with actual prompt
        const response = await quizApi.generateQuiz(prompt, userId);
        setQuestions(response.response.questions);
        setLoading(false);
      } catch (error) {
        console.error("Error generating quiz:", error);
        setLoading(false);
      }
    };

    generateQuiz();
  }, []);

  const handleAnswerSelect = async (answer: string) => {
    setSelectedAnswer(answer);
    const newUserAnswers = {
      ...userAnswers,
      [questions[currentQuestion].question_number]: answer,
    };
    setUserAnswers(newUserAnswers);

    // If this is the last question, submit the quiz
    if (currentQuestion === questions.length - 1) {
      try {
        const userId = "user_50";
        const result = await quizApi.submitQuizAnswers(
          { response: { questions } },
          newUserAnswers,
          userId,
        );
        router.push(
          `/mcq-results?result=${encodeURIComponent(JSON.stringify(result))}`,
        );
      } catch (error) {
        console.error("Error submitting quiz:", error);
      }
    } else {
      // Move to next question after a delay
      setTimeout(() => {
        setCurrentQuestion((prev) => prev + 1);
        setSelectedAnswer(null);
      }, 1000);
    }
  };

  if (loading) {
    return <div>Loading quiz...</div>;
  }

  // if (questions.length === 0) {
  //   return <NoQuestionsMessage />;
  // }

  const currentQ = questions[currentQuestion];

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl p-6 space-y-6">
        <h2 className="text-2xl font-bold text-center mb-6">
          {currentQ.question}
        </h2>
        <div className="grid grid-cols-1 gap-4">
          {currentQ.options.map((option, index) => (
            <Button
              key={index}
              variant="outline"
              className={`p-4 text-lg justify-start h-auto ${
                selectedAnswer === option
                  ? selectedAnswer === currentQ.answer
                    ? "border-green-500 border-2"
                    : "border-red-500 border-2"
                  : ""
              } rounded-xl shadow-md transition-all duration-300 hover:shadow-lg`}
              onClick={() => handleAnswerSelect(option)}
              disabled={selectedAnswer !== null}
            >
              {option}
            </Button>
          ))}
        </div>
        <div className="text-center text-sm text-gray-500">
          Question {currentQuestion + 1} of {questions.length}
        </div>
      </Card>
    </div>
  );
}
