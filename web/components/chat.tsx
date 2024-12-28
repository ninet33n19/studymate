"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import removeMd from "remove-markdown";

type Message = {
  role: "user" | "assistant";
  content: string;
  doc?: string;
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:5000/chatbot", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: input,
          params: {
            user_id: "user_2", // You might want to generate this dynamically
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      const assistantMessage: Message = {
        role: "assistant",
        content: removeMd(data.response.generated_text),
        doc: removeMd(data.response.params),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error:", error);
      // Handle error (e.g., show an error message to the user)
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-screen h-screen flex">
      <Card className="w-full h-full mx-auto">
        <CardContent className="p-6 h-full flex flex-col">
          <ScrollArea className="flex-grow pr-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                } mb-4`}
              >
                <div
                  className={`flex items-start ${
                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
                >
                  <Avatar className="w-8 h-8">
                    <AvatarImage
                      src={
                        message.role === "user"
                          ? "/user-avatar.png"
                          : "/bot-avatar.png"
                      }
                    />
                    <AvatarFallback>
                      {message.role === "user" ? "U" : "AI"}
                    </AvatarFallback>
                  </Avatar>
                  <div
                    className={`mx-2 p-3 rounded-lg ${
                      message.role === "user"
                        ? "bg-blue-500 text-white"
                        : "bg-gray-200 dark:bg-gray-700"
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="text-gray-500 text-sm mb-1">
                        {message.doc}
                      </div>
                    )}
                    {message.content}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </ScrollArea>
          <form onSubmit={handleSubmit} className="mt-4 flex">
            <Input
              type="text"
              placeholder="Type your message here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-grow mr-2"
            />
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Sending..." : "Send"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
