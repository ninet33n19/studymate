import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function RegisterDetailsPage() {
  return (
    <div className="flex min-h-screen bg-blue-50 justify-center items-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-3xl font-bold text-center text-blue-800">
            Additional Details
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form>
            <div className="space-y-4">
              <div className="space-y-2">
                <label
                  htmlFor="name"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-blue-700"
                >
                  Name
                </label>
                <Input
                  id="name"
                  placeholder="Your full name"
                  className="w-full border-blue-200 focus:border-green-500 focus:ring-green-500"
                />
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="domain"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-blue-700"
                >
                  Domain of Study
                </label>
                <Select>
                  <SelectTrigger className="w-full border-blue-200 focus:border-green-500 focus:ring-green-500">
                    <SelectValue placeholder="Select your domain" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cs">Computer Science</SelectItem>
                    <SelectItem value="engineering">Engineering</SelectItem>
                    <SelectItem value="business">Business</SelectItem>
                    <SelectItem value="arts">Arts</SelectItem>
                    <SelectItem value="science">Science</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label
                  htmlFor="year"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-blue-700"
                >
                  Year of Study
                </label>
                <Select>
                  <SelectTrigger className="w-full border-blue-200 focus:border-green-500 focus:ring-green-500">
                    <SelectValue placeholder="Select your year" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">First Year</SelectItem>
                    <SelectItem value="2">Second Year</SelectItem>
                    <SelectItem value="3">Third Year</SelectItem>
                    <SelectItem value="4">Fourth Year</SelectItem>
                    <SelectItem value="5">Fifth Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <Button className="w-full bg-green-600 hover:bg-green-700 text-white">
            Complete Registration
          </Button>
          <Button
            variant="link"
            className="w-full text-blue-700 hover:text-blue-900"
            asChild
          >
            <Link href="/login">Back to Login</Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
