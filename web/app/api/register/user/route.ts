import { NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../../auth/[...nextauth]/route";
import connectDB from "@/lib/mongodb";
import User from "@/models/User";

export async function POST(request: Request) {
  try {
    // Get the session to verify the user is authenticated
    const session = await getServerSession(authOptions);

    if (!session || !session.user) {
      return NextResponse.json(
        { error: "You must be logged in to update your profile" },
        { status: 401 },
      );
    }

    // Connect to the database
    await connectDB();

    // Get the request body
    const { name, domain, year } = await request.json();

    // Validate the input
    if (!name || !domain || !year) {
      return NextResponse.json(
        { error: "All fields are required" },
        { status: 400 },
      );
    }

    // Update or create the user profile
    const userProfile = await User.findOneAndUpdate(
      { userId: session.user.id },
      {
        userId: session.user.id,
        email: session.user.email,
        name,
        domain,
        yearOfStudy: year,
        profileCompleted: true,
        updatedAt: new Date(),
      },
      { upsert: true, new: true },
    );

    return NextResponse.json({
      message: "Profile updated successfully",
      user: userProfile,
    });
  } catch (error) {
    console.error("Profile update error:", error);
    return NextResponse.json(
      { error: "Failed to update profile" },
      { status: 500 },
    );
  }
}

// Optional: Add a GET route to fetch user details
export async function GET() {
  try {
    const session = await getServerSession(authOptions);

    if (!session || !session.user) {
      return NextResponse.json(
        { error: "You must be logged in to view your profile" },
        { status: 401 },
      );
    }

    await connectDB();

    const userProfile = await User.findOne({ userId: session.user.id });

    if (!userProfile) {
      return NextResponse.json({ error: "Profile not found" }, { status: 404 });
    }

    return NextResponse.json({ user: userProfile });
  } catch (error) {
    console.error("Profile fetch error:", error);
    return NextResponse.json(
      { error: "Failed to fetch profile" },
      { status: 500 },
    );
  }
}
