"use client";

import { useState, useEffect } from "react";
import { Search, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Badge } from "@/components/ui/badge";
import { Sidebar } from "@/components/sidebar";
import { CourseCard } from "@/components/course-card";
import { GradesSection } from "@/components/grades-section";

export default function DashboardPage() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-100 dark:from-gray-950 dark:to-indigo-950 transition-colors duration-200">
      <div className="flex">
        <Sidebar darkMode={darkMode} />

        {/* Main Content with New Layout */}
        <div className="flex-1 flex flex-col">
          {/* Header - Now sticky and with new styling */}
          <header className="sticky top-0 z-10 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-indigo-100 dark:border-indigo-900">
            <div className="flex items-center justify-between px-6 py-4">
              <h1 className="text-2xl font-bold text-indigo-800 dark:text-indigo-200">
                Dashboard
              </h1>
              <div className="flex items-center gap-4">
                <div className="relative">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-indigo-400" />
                  <Input
                    placeholder="Search..."
                    className="pl-8 w-[250px] border-indigo-200 dark:border-indigo-800 bg-white/50 dark:bg-gray-800/50 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex items-center space-x-2 bg-white/50 dark:bg-gray-800/50 rounded-lg p-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900"
                  >
                    <span className="sr-only">Notifications</span>
                    🔔
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900"
                  >
                    <span className="sr-only">Messages</span>
                    ✉️
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-indigo-600 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900"
                  >
                    <span className="sr-only">Chat</span>
                    💬
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDarkMode(!darkMode)}
                    className="text-indigo-600 dark:text-indigo-300"
                  >
                    {darkMode ? (
                      <Sun className="h-5 w-5" />
                    ) : (
                      <Moon className="h-5 w-5" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </header>

          {/* Main Grid Layout */}
          <div className="flex-1 p-6">
            <div className="mx-auto max-w-7xl grid grid-cols-12 gap-6">
              {/* Courses Section - Wider */}
              <div className="col-span-12 lg:col-span-8 space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <CourseCard
                    title="System Fundamentals"
                    subtitle="Learn the basics of computer systems"
                    progress={67}
                    lesson="Lesson 8 out of 12"
                    icon="💻"
                  />
                  <CourseCard
                    title="Computer Networks"
                    subtitle="Learn about computer networks"
                    progress={33}
                    lesson="Lesson 4 out of 12"
                    icon="🌐"
                    badge="Due Homework"
                  />
                  <CourseCard
                    title="Data Structures"
                    subtitle="Learn about data structures"
                    progress={50}
                    lesson="Understanding linked lists"
                    icon="📊"
                    badge="Open Exam"
                  />
                  <CourseCard
                    title="Database Management"
                    subtitle="Learn about database management"
                    progress={100}
                    lesson="Pending concepts for MySQL"
                    icon="🗄️"
                  />
                </div>

                {/* Calendar moved to main section */}
                <Card className="border-indigo-200 dark:border-indigo-800 bg-white/80 dark:bg-gray-900/80 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-indigo-800 dark:text-indigo-200">
                      Your Schedule
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Calendar
                      mode="multiple"
                      className="rounded-md border-indigo-200 dark:border-indigo-800"
                    />
                  </CardContent>
                </Card>
              </div>

              {/* Right Column - Current, Grades, Inbox */}
              <div className="col-span-12 lg:col-span-4 space-y-6">
                {/* Current Section */}
                <Card className="border-indigo-200 dark:border-indigo-800 bg-white/80 dark:bg-gray-900/80 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-indigo-800 dark:text-indigo-200">
                      Current
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <h3 className="font-semibold text-indigo-800 dark:text-indigo-200">
                      DSA Basics
                    </h3>
                    <div className="mt-2 space-y-2 text-indigo-600 dark:text-indigo-300">
                      <div className="flex justify-between">
                        <span>Currently embedded:</span>
                        <span>34/40</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Presence:</span>
                        <span>Mandatory</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Ends in:</span>
                        <span>45 min</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <GradesSection />

                {/* Inbox Section */}
                <Card className="border-indigo-200 dark:border-indigo-800 bg-white/80 dark:bg-gray-900/80 shadow-lg">
                  <CardHeader>
                    <CardTitle className="text-indigo-800 dark:text-indigo-200">
                      Inbox
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <h3 className="font-medium text-indigo-800 dark:text-indigo-200">
                      Your document has been categorized
                    </h3>
                    <p className="mt-2 text-indigo-600 dark:text-indigo-300">
                      Need help studying? Contact our AI assistant for more
                      information.
                    </p>
                    <Button
                      variant="outline"
                      className="mt-4 w-full border-indigo-300 dark:border-indigo-700 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/50"
                    >
                      View Details
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
