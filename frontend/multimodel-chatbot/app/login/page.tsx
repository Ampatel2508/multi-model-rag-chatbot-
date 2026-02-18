"use client";

import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSignIn = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await signIn("google", {
        redirect: false,
        callbackUrl: "/chat",
      });

      if (result?.error) {
        setError("Failed to sign in. Please try again.");
        console.error("Sign in error:", result.error);
      } else if (result?.ok) {
        router.push("/chat");
      }
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
      console.error("Error during sign in:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-2xl p-8">
          {/* Logo/Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              Multi-Model Chatbot
            </h1>
            <p className="text-gray-600">Sign in with your Google account</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
              {error}
            </div>
          )}

          {/* Google Sign In Button */}
          <Button
            onClick={handleGoogleSignIn}
            disabled={isLoading}
            className="w-full h-12 bg-white text-gray-800 border-2 border-gray-300 hover:bg-gray-50 font-semibold text-lg mb-4 flex items-center justify-center gap-3"
          >
            {isLoading ? (
              <>
                <span className="inline-block animate-spin">⏳</span>
                Signing in...
              </>
            ) : (
              <>
                <svg
                  className="w-6 h-6"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Sign in with Google
              </>
            )}
          </Button>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">OR</span>
            </div>
          </div>

          {/* Info Section */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center text-sm text-gray-700">
            <p className="font-semibold mb-2">🔐 Secure Login</p>
            <p>
              We use Google OAuth for secure authentication. Your data is protected and never shared.
            </p>
          </div>

          {/* Features List */}
          <div className="mt-8 space-y-2 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Multi-model AI chatbot</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Chat history persistence</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span>Document upload & analysis</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
