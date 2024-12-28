"use client";

import { useState } from "react";
import Flashcard from "./Flashcard";
import { Button } from "@/components/ui/button";

// Sample flashcards data (replace with your own or fetch from an API)
const flashcardsData = [
  { id: 1, question: "What is the capital of France?", answer: "Paris" },
  { id: 2, question: "What is 2 + 2?", answer: "4" },
  {
    id: 3,
    question: 'Who wrote "Romeo and Juliet"?',
    answer: "William Shakespeare",
  },
];

export default function FlashcardGame() {
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [knownCount, setKnownCount] = useState(0);
  const [unknownCount, setUnknownCount] = useState(0);
  const [isShowingAnswer, setIsShowingAnswer] = useState(false);

  const handleKnow = () => {
    setKnownCount(knownCount + 1);
    nextCard();
  };

  const handleDontKnow = () => {
    setUnknownCount(unknownCount + 1);
    nextCard();
  };

  const nextCard = () => {
    setCurrentCardIndex((prevIndex) => (prevIndex + 1) % flashcardsData.length);
    setIsShowingAnswer(false);
  };

  const handleFlip = () => {
    setIsShowingAnswer(!isShowingAnswer);
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-4 -mt-20">
      <div className="mb-4 text-lg font-medium text-muted-foreground">
        {isShowingAnswer ? "Showing Answer" : "Showing Question"}
      </div>
      <div className="mb-8" onClick={handleFlip}>
        <Flashcard
          question={flashcardsData[currentCardIndex].question}
          answer={flashcardsData[currentCardIndex].answer}
        />
      </div>
      <div className="flex gap-6 mt-4">
        <Button onClick={handleDontKnow} variant="outline" size="lg">
          Don't Know
        </Button>
        <Button onClick={handleKnow} size="lg">
          Know
        </Button>
      </div>
      <div className="mt-8 text-center text-lg">
        <p className="mb-2">Known: {knownCount}</p>
        <p>Unknown: {unknownCount}</p>
      </div>
    </div>
  );
}
