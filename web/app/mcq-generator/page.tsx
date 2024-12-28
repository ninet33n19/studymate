"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useRouter } from "next/navigation";

interface Question {
  id: number;
  text: string;
  options: string[];
  correctAnswer: number;
}

const questions: Question[] = [
  {
    id: 1,
    text: "What is the capital of France?",
    options: ["London", "Berlin", "Paris", "Madrid"],
    correctAnswer: 2,
  },
  {
    id: 2,
    text: "Which planet is known as the Red Planet?",
    options: ["Venus", "Mars", "Jupiter", "Saturn"],
    correctAnswer: 1,
  },
  {
    id: 3,
    text: "Who painted the Mona Lisa?",
    options: [
      "Vincent van Gogh",
      "Pablo Picasso",
      "Leonardo da Vinci",
      "Michelangelo",
    ],
    correctAnswer: 2,
  },
];

export default function MCQGenerator() {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [score, setScore] = useState(0);
  const [answeredQuestions, setAnsweredQuestions] = useState(0);
  const router = useRouter();

  useEffect(() => {
    if (selectedAnswer !== null) {
      const timer = setTimeout(() => {
        if (currentQuestion + 1 < questions.length) {
          setCurrentQuestion((prev) => prev + 1);
          setSelectedAnswer(null);
          setIsCorrect(null);
        } else {
          // Store the current result in local storage
          const previousResults = JSON.parse(
            localStorage.getItem("quizResults") || "[]",
          );
          const newResult = {
            score,
            total: questions.length,
            date: new Date().toISOString(),
          };
          localStorage.setItem(
            "quizResults",
            JSON.stringify([...previousResults, newResult]),
          );

          router.push(`/mcq-results?score=${score}&total=${questions.length}`);
        }
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [selectedAnswer, currentQuestion, score, router]);

  const handleAnswerSelect = (index: number) => {
    setSelectedAnswer(index);
    const correct = index === questions[currentQuestion].correctAnswer;
    setIsCorrect(correct);
    if (correct) {
      setScore((prev) => prev + 1);
    }
    setAnsweredQuestions((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl p-6 space-y-6">
        <h2 className="text-2xl font-bold text-center mb-6">
          {questions[currentQuestion].text}
        </h2>
        <div className="grid grid-cols-1 gap-4">
          {questions[currentQuestion].options.map((option, index) => (
            <Button
              key={index}
              variant="outline"
              className={`p-4 text-lg justify-start h-auto ${
                selectedAnswer === index
                  ? isCorrect
                    ? "border-green-500 border-2"
                    : "border-red-500 border-2"
                  : ""
              } rounded-xl shadow-md transition-all duration-300 hover:shadow-lg`}
              onClick={() => handleAnswerSelect(index)}
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
