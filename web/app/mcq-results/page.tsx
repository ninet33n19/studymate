"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import Link from "next/link";
import {
  Line,
  LineChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface QuizResult {
  score: number;
  total: number;
  date: string;
}

export default function MCQResults() {
  const searchParams = useSearchParams();
  const score = parseInt(searchParams.get("score") || "0", 10);
  const total = parseInt(searchParams.get("total") || "0", 10);
  const wrongAnswers = total - score;
  const percentage = ((score / total) * 100).toFixed(2);

  const [chartData, setChartData] = useState<QuizResult[]>([]);

  useEffect(() => {
    const storedResults = JSON.parse(
      localStorage.getItem("quizResults") || "[]",
    );
    setChartData(storedResults.slice(-5)); // Get the last 5 results
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl p-6 space-y-6">
        <h2 className="text-3xl font-bold text-center mb-6">Quiz Results</h2>
        <div className="space-y-4">
          <p className="text-xl text-center">
            You scored <span className="font-bold text-green-600">{score}</span>{" "}
            out of <span className="font-bold">{total}</span>
          </p>
          <p className="text-lg text-center">
            Percentage: <span className="font-bold">{percentage}%</span>
          </p>
          <div className="flex justify-center space-x-4">
            <div className="text-center">
              <p className="text-sm text-gray-500">Correct Answers</p>
              <p className="text-2xl font-bold text-green-600">{score}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">Wrong Answers</p>
              <p className="text-2xl font-bold text-red-600">{wrongAnswers}</p>
            </div>
          </div>
        </div>

        <div className="mt-8">
          <h3 className="text-xl font-bold text-center mb-4">
            Performance History
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => new Date(value).toLocaleDateString()}
                style={{ fontSize: "0.8rem" }}
              />
              <YAxis style={{ fontSize: "0.8rem" }} />
              <Tooltip
                labelFormatter={(value) => new Date(value).toLocaleDateString()}
                formatter={(value: number, name: string) => [
                  value,
                  name === "score" ? "Score" : "Total",
                ]}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="score"
                stroke="#8884d8"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name="Score"
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#82ca9d"
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
                name="Total Questions"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="flex justify-center mt-6">
          <Link href="/mcq-generator" passHref>
            <Button>Try Again</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
