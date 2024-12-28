import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const body = await request.json();

  const response = await fetch("http://localhost:3000/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (response.ok) {
    return NextResponse.json(data);
  } else {
    return NextResponse.json(data, { status: response.status });
  }
}
