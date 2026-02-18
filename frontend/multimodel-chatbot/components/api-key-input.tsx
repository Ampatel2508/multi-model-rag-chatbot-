"use client";

import { useState, useCallback } from "react";
import { Key, ExternalLink, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { detectProvider, providers, type Provider } from "@/lib/providers";

interface ApiKeyInputProps {
  onApiKeySubmit: (apiKey: string, provider: Provider) => void;
}

export function ApiKeyInput({ onApiKeySubmit }: ApiKeyInputProps) {
  const [apiKey, setApiKey] = useState("");
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detectedProvider, setDetectedProvider] = useState<Provider | null>(null);

  const handleKeyChange = useCallback((value: string) => {
    setApiKey(value);
    setError(null);
    const provider = detectProvider(value);
    setDetectedProvider(provider);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!apiKey.trim()) {
      setError("Please enter an API key");
      return;
    }

    const provider = detectProvider(apiKey);
    if (!provider) {
      setError("Could not detect provider. Please ensure your API key is from Gemini, OpenRouter, or Groq.");
      return;
    }

    setIsValidating(true);
    setError(null);

    try {
      // Validate by trying to fetch models
      const response = await fetch("/api/models", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, apiKey }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to validate API key");
      }

      const data = await response.json();
      
      if (!data.success || !data.models || data.models.length === 0) {
        throw new Error("No models available for this provider");
      }

      // Success - proceed to chat
      onApiKeySubmit(apiKey, provider);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid API key or network error");
    } finally {
      setIsValidating(false);
    }
  };

  const providerConfig = detectedProvider
    ? providers.find((p) => p.key === detectedProvider)
    : null;

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
          <Key className="w-8 h-8 text-primary" />
        </div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Multi-Model AI Chat</h1>
        <p className="text-muted-foreground">
          Enter your API key to start chatting with AI models and upload documents for context
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <Input
            type="password"
            value={apiKey}
            onChange={(e) => handleKeyChange(e.target.value)}
            placeholder="Enter your API key..."
            className="pr-12 h-12 text-base"
            disabled={isValidating}
          />
          {detectedProvider && !isValidating && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">
              <CheckCircle2 className="w-5 h-5 text-green-500" />
            </div>
          )}
        </div>

        {detectedProvider && providerConfig && !error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
            <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />
            <span className="text-sm text-green-700 dark:text-green-400">
              Detected: <strong>{providerConfig.name}</strong> - {providerConfig.description}
            </span>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
            <AlertCircle className="w-5 h-5 text-destructive shrink-0" />
            <span className="text-sm text-destructive">{error}</span>
          </div>
        )}

        <Button type="submit" className="w-full h-12" disabled={!apiKey.trim() || isValidating}>
          {isValidating ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Validating & Fetching Models...
            </>
          ) : (
            "Continue"
          )}
        </Button>
      </form>

      <div className="mt-8">
        <h2 className="text-lg font-semibold text-foreground mb-4 text-center">
          {"Don't have an API key? Get one here:"}
        </h2>
        <div className="grid gap-3">
          {providers.map((provider) => (
            <a
              key={provider.key}
              href={provider.apiKeyLink}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between p-4 rounded-lg border border-border bg-card hover:bg-accent transition-colors group"
            >
              <div>
                <h3 className="font-medium text-foreground group-hover:text-primary transition-colors">
                  {provider.name}
                </h3>
                <p className="text-sm text-muted-foreground">{provider.description}</p>
              </div>
              <ExternalLink className="w-5 h-5 text-muted-foreground group-hover:text-primary transition-colors" />
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}