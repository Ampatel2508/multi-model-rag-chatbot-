"use client";

import { useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function Home() {
  const { data: session, status } = useSession();
  const router = useRouter();

  // Redirect based on authentication status
  useEffect(() => {
    if (status === "loading") {
      return; // Wait for session to load
    }

    if (status === "authenticated") {
      // If user is authenticated, redirect to chat
      router.push("/chat");
    } else {
      // If user is not authenticated, redirect to login
      router.push("/login");
    }
  }, [status, router]);

  // Show loading state while checking authentication
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
}