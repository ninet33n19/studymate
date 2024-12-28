import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import connectDB from "@/lib/mongodb";
import CredentialsUser from "@/models/CredentialsUser";

export async function POST(request: Request) {
  try {
    await connectDB();

    const { email, password } = await request.json();

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { error: "Email and password are required" },
        { status: 400 },
      );
    }

    // Check if user already exists
    const existingUser = await CredentialsUser.findOne({ email });
    if (existingUser) {
      return NextResponse.json(
        { error: "Email already registered" },
        { status: 409 },
      );
    }

    // Create new user
    const user = await CredentialsUser.create({
      email,
      password, // Password will be hashed by the pre-save hook
    });

    // Return user data (excluding password)
    return NextResponse.json({
      user: {
        id: user._id,
        email: user.email,
      },
    });
  } catch (error) {
    console.error("Registration error:", error);
    return NextResponse.json(
      { error: "Internal server error hehehe" },
      { status: 500 },
    );
  }
}
