"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User, LogOut, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ModelSelector } from "@/components/model-selector";
import { DocumentUploader } from "@/components/document-uploader";
import { URLInput } from "@/components/url-input";
import { getProviderConfig, type Provider } from "@/lib/providers";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ filename?: string; page?: number }>;
}

interface ChatInterfaceProps {
  apiKey: string;
  provider: Provider;
  onReset: () => void;
  userId?: string;
}

export function ChatInterface({ apiKey, provider, onReset, userId }: ChatInterfaceProps) {
  const providerConfig = getProviderConfig(provider);
  const [selectedModel, setSelectedModel] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [documentIds, setDocumentIds] = useState<string[]>([]);
  const [url, setUrl] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedModel) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    const userInput = input; // Save user input before clearing
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userInput,
          apiKey,
          provider,
          model: selectedModel,
          documentIds,
          url: url || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Failed to get response");
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Auto-schedule meetings to Google Calendar
      await scheduleToGoogleCalendar(userInput, data.answer);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Something went wrong"}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const scheduleToGoogleCalendar = async (userInput: string, responseText: string) => {
    try {
      console.log("Auto-scheduling to Google Calendar");
      console.log("User input:", userInput);
      console.log("LLM response:", responseText);
      
      // Extract meeting info from response
      const dateMatch = responseText.match(/(\d{1,2})\s*[–\-]?\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b/i);
      const timeMatch = responseText.match(/(\d{1,2}):(\d{2})\s*(am|pm)?\s*[–\-]\s*(\d{1,2}):(\d{2})\s*(am|pm)?/i);
      
      if (!dateMatch || !timeMatch) {
        console.log("Meeting pattern not found, skipping auto-scheduling");
        return;
      }

      // Convert times to 24-hour format
      const convertTo24Hour = (hour: string, ampm: string | undefined): string => {
        let h = parseInt(hour);
        if (ampm && ampm.toLowerCase() === 'pm' && h !== 12) h += 12;
        if (ampm && ampm.toLowerCase() === 'am' && h === 12) h = 0;
        return h.toString().padStart(2, '0');
      };

      const startHour = convertTo24Hour(timeMatch[1], timeMatch[3]);
      const endHour = convertTo24Hour(timeMatch[4], timeMatch[6]);
      
      const startTime = `${startHour}:${timeMatch[2]}`;
      const endTime = `${endHour}:${timeMatch[5]}`;

      // Call backend to schedule
      const schedulingResponse = await fetch("/api/schedule-google-meeting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: responseText.split(",")[0] || "Meeting",
          date: `${dateMatch[1]}-${dateMatch[2]}`,
          start_time: startTime,
          end_time: endTime,
          description: responseText,
          user_id: userId,
        }),
      });

      const schedulingData = await schedulingResponse.json();
      console.log("Google Calendar response:", schedulingData);

      if (schedulingData.success) {
        // Add success confirmation to chat
        const confirmationMessage: Message = {
          id: (Date.now() + 100).toString(),
          role: "assistant",
          content: `\n✅ **Meeting Added to Google Calendar**\n📅 Event: ${schedulingData.event_title}\n🕐 Date: ${schedulingData.event_date}\n⏰ Time: ${schedulingData.start_time} - ${schedulingData.end_time}\n🔗 Event ID: ${schedulingData.event_id}`,
        };
        setMessages((prev) => [...prev, confirmationMessage]);
      }
    } catch (error) {
      console.error("Error scheduling to Google Calendar:", error);
    }
  };

  const cancelGoogleMeeting = async (eventId: string) => {
    try {
      const response = await fetch("/api/cancel-google-meeting", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: eventId,
          user_id: userId,
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        const confirmationMessage: Message = {
          id: (Date.now() + 100).toString(),
          role: "assistant",
          content: `✅ Meeting cancelled successfully!\n📅 Removed: ${data.event_title} from Google Calendar`,
        };
        setMessages((prev) => [...prev, confirmationMessage]);
      } else {
        alert(data.message || "Failed to cancel meeting");
      }
    } catch (error) {
      console.error("Error cancelling meeting:", error);
      alert("Failed to cancel meeting");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleModelChange = (model: string) => {
    setSelectedModel(model);
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-80 border-r border-border bg-card p-4 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Settings</h2>
          <Button variant="ghost" size="sm" onClick={onReset} className="gap-2">
            <LogOut className="w-4 h-4" />
            Change
          </Button>
        </div>

        <div className="space-y-4 flex-1 overflow-y-auto">
          <div>
            <label className="text-sm font-medium mb-2 block">Provider</label>
            <div className="p-3 rounded-lg bg-muted text-sm">
              {providerConfig?.name}
            </div>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Model</label>
            <ModelSelector
              provider={provider}
              apiKey={apiKey}
              selectedModel={selectedModel}
              onModelChange={handleModelChange}
            />
          </div>

          <URLInput onUrlChange={setUrl} url={url} />

          <DocumentUploader onDocumentsSelected={setDocumentIds} />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b border-border bg-card px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h1 className="font-semibold text-foreground">AI Assistant</h1>
              <p className="text-xs text-muted-foreground">
                {selectedModel ? `Using ${selectedModel}` : "Select a model to start"}
              </p>
            </div>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <h2 className="text-xl font-semibold text-foreground mb-2">
                Start a conversation
              </h2>
              <p className="text-muted-foreground max-w-md">
                {url || documentIds.length > 0
                  ? `Ready to help! Ask questions about your ${documentIds.length > 0 ? `${documentIds.length} document${documentIds.length > 1 ? "s" : ""}${url ? " and the provided URL" : ""}` : "the provided documentation URL"}`
                  : "Enter a documentation URL or upload documents to get started"}
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex gap-4 max-w-4xl",
                  message.role === "user" ? "ml-auto flex-row-reverse" : ""
                )}
              >
                <div
                  className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  )}
                >
                  {message.role === "user" ? (
                    <User className="w-5 h-5" />
                  ) : (
                    <Bot className="w-5 h-5" />
                  )}
                </div>
                <div className="flex-1 space-y-2">
                  <div
                    className={cn(
                      "rounded-2xl px-5 py-4",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground ml-auto max-w-2xl"
                        : "bg-muted text-foreground max-w-3xl"
                    )}
                  >
                    <p className="text-base leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                  </div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/80 text-xs font-medium border border-muted-foreground/20"
                        >
                          <FileText className="w-4 h-4" />
                          <span>
                            {source.filename}
                            {source.page && ` (p.${source.page})`}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="flex gap-4 max-w-4xl">
              <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center shrink-0">
                <Bot className="w-5 h-5" />
              </div>
              <div className="rounded-2xl px-4 py-3 bg-muted">
                <div className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-border bg-card p-6">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="relative flex items-end gap-2">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={selectedModel ? "Ask a question..." : "Select a model first..."}
                className="resize-none min-h-13 max-h-50 pr-12"
                disabled={isLoading || !selectedModel}
                rows={1}
              />
              <Button
                type="submit"
                size="icon"
                className="absolute right-2 bottom-2 h-10 w-10"
                disabled={!input.trim() || isLoading || !selectedModel}
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2 text-center">
              Press Enter to send, Shift + Enter for new line
            </p>
          </form>
        </div>
      </div>
    </div>
  );
}