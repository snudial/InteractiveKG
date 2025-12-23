







"use server";

import { NextResponse } from "next/server";

export async function POST() {
  try {
    const answer = await fetch(process.env.API_URL + "/reset_dbms", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-store",
    });
    if (answer.status != 200) {
      return NextResponse.json({ message: "error" });
    }
  } catch (e) {
    return NextResponse.json({ message: "failed" });
  }

  return NextResponse.json({
    message: "success",
  });
}
