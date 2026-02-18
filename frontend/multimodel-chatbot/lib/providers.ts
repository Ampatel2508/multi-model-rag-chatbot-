export type Provider = "gemini" | "openrouter" | "groq";

export interface ProviderConfig {
  name: string;
  key: Provider;
  models: { id: string; name: string }[];
  apiKeyLink: string;
  apiKeyPlaceholder: string;
  description: string;
}

export const providers: ProviderConfig[] = [
  {
    name: "Google Gemini",
    key: "gemini",
    models: [
      { id: "gemini-2.0-flash", name: "Gemini 2.0 Flash" },
      { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash" },
      { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro" },
      { id: "gemini-pro", name: "Gemini Pro" },
    ],
    apiKeyLink: "https://aistudio.google.com/app/apikey",
    apiKeyPlaceholder: "Enter your Gemini API key (starts with AI...)",
    description: "Google's most capable AI models",
  },
  {
    name: "OpenRouter",
    key: "openrouter",
    models: [
      { id: "openai/gpt-4-turbo", name: "GPT-4 Turbo" },
      { id: "openai/gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
      { id: "anthropic/claude-3-opus", name: "Claude 3 Opus" },
      { id: "anthropic/claude-3-sonnet", name: "Claude 3 Sonnet" },
      { id: "anthropic/claude-3-haiku", name: "Claude 3 Haiku" },
      { id: "meta-llama/llama-3-70b-instruct", name: "Llama 3 70B" },
      { id: "mistralai/mixtral-8x7b-instruct", name: "Mixtral 8x7B" },
    ],
    apiKeyLink: "https://openrouter.ai/keys",
    apiKeyPlaceholder: "Enter your OpenRouter API key (starts with sk-or-...)",
    description: "Access multiple AI providers through one API",
  },
  {
    name: "Groq",
    key: "groq",
    models: [
      { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B Versatile" },
      { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B Instant" },
      { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B" },
      { id: "gemma2-9b-it", name: "Gemma 2 9B" },
    ],
    apiKeyLink: "https://console.groq.com/keys",
    apiKeyPlaceholder: "Enter your Groq API key (starts with gsk_...)",
    description: "Ultra-fast inference with open source models",
  },
];

export function detectProvider(apiKey: string): Provider | null {
  if (!apiKey) return null;
  if (apiKey.startsWith("AI")) return "gemini";
  if (apiKey.startsWith("sk-or-")) return "openrouter";
  if (apiKey.startsWith("gsk_")) return "groq";
  return null;
}

export function getProviderConfig(provider: Provider): ProviderConfig | undefined {
  return providers.find((p) => p.key === provider);
}
