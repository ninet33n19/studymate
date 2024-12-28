"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/hooks/use-toast";
import { signIn } from "next-auth/react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Input } from "@/components/ui/input";

export default function RegisterPage() {
  const [email, setEmail] = useState("meet.djsce@gmail.com");
  const [password, setPassword] = useState("pass@123");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const { toast } = useToast();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const registerRes = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      let data;
      try {
        data = await registerRes.json();
      } catch (error) {
        throw new Error("Invalid response from server");
      }

      if (registerRes.ok) {
        // If registration is successful, automatically sign them in
        const signInResult = await signIn("credentials", {
          email,
          password,
          redirect: false,
        });

        if (signInResult?.error) {
          toast({
            title: "Authentication Failed",
            description:
              "Registration successful but couldn't log you in automatically. Please try logging in.",
            variant: "destructive",
          });
          router.push("/login");
        } else {
          toast({
            title: "Registration Successful",
            description: "Please complete your profile details",
          });
          router.push("/register/details");
        }
      } else {
        toast({
          title: "Registration Failed",
          description: data.error || "An error occurred during registration",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Error:", error);
      toast({
        title: "Registration Error",
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleRegister = async () => {
    setIsLoading(true);
    try {
      const result = await signIn("google", {
        redirect: false,
        callbackUrl: "/register/details",
      });

      if (result?.error) {
        toast({
          title: "Authentication Failed",
          description: "Failed to sign in with Google",
          variant: "destructive",
        });
      } else {
        router.push("/register/details");
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "An error occurred during Google sign-in",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-blue-50">
      <Card className="flex-1 rounded-none shadow-2xl z-10 flex flex-col justify-center items-center bg-white">
        <div className="w-full max-w-md p-8">
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center text-blue-800">
              Create Account
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegister}>
              <div className="space-y-4">
                <div className="space-y-2">
                  <label
                    htmlFor="email"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-blue-700"
                  >
                    Email
                  </label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="m@example.com"
                    className="w-full border-blue-200 focus:border-green-500 focus:ring-green-500"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <label
                    htmlFor="password"
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 text-blue-700"
                  >
                    Password
                  </label>
                  <Input
                    id="password"
                    type="password"
                    className="w-full border-blue-200 focus:border-green-500 focus:ring-green-500"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={isLoading}
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-green-600 hover:bg-green-700 text-white"
                  disabled={isLoading}
                >
                  {isLoading ? "Processing..." : "Register"}
                </Button>
              </div>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <div className="relative w-full">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-blue-200" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-blue-600">
                  Or continue with
                </span>
              </div>
            </div>
            <Button
              variant="outline"
              className="w-full border-blue-200 text-blue-700 hover:bg-blue-50"
              onClick={handleGoogleRegister}
              disabled={isLoading}
            >
              <svg
                className="mr-2 h-4 w-4"
                aria-hidden="true"
                focusable="false"
                data-prefix="fab"
                data-icon="google"
                role="img"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 488 512"
              >
                <path
                  fill="currentColor"
                  d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"
                ></path>
              </svg>
              {isLoading ? "Processing..." : "Google"}
            </Button>
            <Button
              variant="link"
              className="w-full text-blue-700 hover:text-blue-900"
              asChild
              disabled={isLoading}
            >
              <Link href="/login">Already have an account? Login here</Link>
            </Button>
          </CardFooter>
        </div>
      </Card>
      <div className="relative flex-1 hidden md:block">
        {/* Image section */}
      </div>
    </div>
  );
}
