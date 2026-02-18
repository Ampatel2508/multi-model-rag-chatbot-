"use client";
import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { ApiKeyInput } from "@/components/api-key-input";
import { ChatInterface } from "@/components/chat-interface-new";
import { Provider } from "@/lib/providers";

export default function ChatPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider | null>(null);
  
  const userId = (session?.user as any)?.id || "";

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    }
  }, [status, router]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return null; // Will be redirected by useEffect
  }

  const handleApiKeySubmit = (key: string, detectedProvider: Provider) => {
    setApiKey(key);
    setProvider(detectedProvider);
  };

  const handleReset = () => {
    setApiKey(null);
    setProvider(null);
  };

  return (
    <main className="min-h-screen w-full">
      {!apiKey || !provider ? (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
          <div className="max-w-md w-full">
            <div className="bg-white rounded-xl shadow-2xl p-8">
              <div className="text-center mb-8">
                <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 mb-2">
                  Welcome Back
                </h1>
                <p className="text-slate-600">Set up your API key to get started</p>
              </div>
              <ApiKeyInput onApiKeySubmit={handleApiKeySubmit} />
            </div>
          </div>
        </div>
      ) : (
        <ChatInterface 
          apiKey={apiKey} 
          provider={provider} 
          onReset={handleReset}
          userId={userId}
        />
      )}
    </main>
  );
}
