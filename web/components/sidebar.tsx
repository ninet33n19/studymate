import Link from "next/link";
import {
  LayoutDashboard,
  FileText,
  Book,
  Users,
  BotIcon as Robot,
  MapIcon as RoadMap,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface SidebarProps {
  darkMode: boolean;
}

export function Sidebar({ darkMode }: SidebarProps) {
  return (
    <aside
      className={`w-[250px] border-r border-gray-200 dark:border-gray-700 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-900"} p-6`}
    >
      {/* Profile Section */}
      <div className="mb-6 flex items-center gap-3">
        <Avatar>
          <AvatarImage src="/placeholder.svg" />
          <AvatarFallback className="bg-gray-200 dark:bg-gray-700">
            AI
          </AvatarFallback>
        </Avatar>
        <div>
          <h2 className="font-semibold">AIStudy</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            example@mail.com
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2">
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg ${darkMode ? "bg-[#FF8000] text-white" : "bg-[#FF8000] text-white"} px-3 py-2`}
        >
          <LayoutDashboard className="h-5 w-5" />
          Dashboard
        </Link>
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <FileText className="h-5 w-5" />
          Documents
        </Link>
        {/* <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <FileText className="h-5 w-5" />
          My Documents
        </Link> */}
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <Book className="h-5 w-5" />
          Subjects
        </Link>
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <Users className="h-5 w-5" />
          Teamspace
        </Link>
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <Robot className="h-5 w-5" />
          My AI
        </Link>
        <Link
          href="#"
          className={`flex items-center gap-3 rounded-lg px-3 py-2 ${darkMode ? "text-gray-300 hover:bg-gray-800" : "text-gray-700 hover:bg-gray-100"}`}
        >
          <RoadMap className="h-5 w-5" />
          Roadmap Generation
        </Link>
      </nav>
    </aside>
  );
}
