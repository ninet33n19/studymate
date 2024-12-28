import { getToken } from "next-auth/jwt";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  const token = await getToken({ req: request });

  // Protected routes
  if (request.nextUrl.pathname.startsWith("/register/details")) {
    if (!token) {
      return NextResponse.redirect(new URL("/login", request.url));
    }

    // Optional: Check if user has already completed details
    // If they have, redirect to dashboard
    // This requires you to store this information in the token
    if (token.hasCompletedDetails) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/register/details/:path*"],
};
