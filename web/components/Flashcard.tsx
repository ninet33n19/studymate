"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";

interface FlashcardProps {
  question: string;
  answer: string;
}

export default function Flashcard({ question, answer }: FlashcardProps) {
  const [isFlipped, setIsFlipped] = useState(false);

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  return (
    <div
      className="relative h-[400px] w-[600px] cursor-pointer [perspective:1000px]"
      onClick={handleFlip}
    >
      <div
        className={`absolute h-full w-full transition-all duration-500 [transform-style:preserve-3d] ${
          isFlipped ? "[transform:rotateY(180deg)]" : ""
        }`}
      >
        <Card className="absolute h-full w-full [backface-visibility:hidden] shadow-lg">
          <CardContent className="flex h-full items-center justify-center p-8 text-center">
            <p className="text-3xl font-semibold">{question}</p>
          </CardContent>
        </Card>
        <Card className="absolute h-full w-full [backface-visibility:hidden] shadow-lg [transform:rotateY(180deg)]">
          <CardContent className="flex h-full items-center justify-center p-8 text-center">
            <p className="text-3xl font-semibold">{answer}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
