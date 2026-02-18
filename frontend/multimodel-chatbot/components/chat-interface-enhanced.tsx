"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User, LogOut, FileText, Calendar, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ModelSelector } from "@/components/model-selector";
import { DocumentUploader } from "@/components/document-uploader";
import { URLInput } from "@/components/url-input";
import { CalendarComponent } from "@/components/calendar";
import { ChatHistory } from "@/components/chat-history";
import { getProviderConfig, type Provider } from "@/lib/providers";
import { cn } from "@/lib/utils";
import { v4 as uuidv4 } from "uuid";

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
  const [showHistory, setShowHistory] = useState(false);
  const [showCalendar, setShowCalendar] = useState(true);
  const [sessionId, setSessionId] = useState<string>("");
  const [generatedUserId] = useState<string>(uuidv4());
  const finalUserId = userId || generatedUserId;
  const [allSessions, setAllSessions] = useState<any[]>([]);
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [calendarRefresh, setCalendarRefresh] = useState(0); // Trigger calendar refresh
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load user's sessions on component mount
  useEffect(() => {
    const loadUserSessions = async () => {
      console.log("[App] Loading sessions for userId:", finalUserId);
      try {
        const response = await fetch(`/api/chat-sessions/${finalUserId}`);
        if (!response.ok) {
          console.warn("[App] Failed to load sessions:", response.status);
          // No previous sessions - create a new one
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          setMessages([]);
          setAllMessages([]);
          return;
        }
        
        const data = await response.json();
        const sessions = data.sessions || [];
        console.log("[App] Loaded sessions:", sessions.length);
        setAllSessions(sessions);

        // Load ALL previous messages from all sessions for context
        let allPreviousMessages: Message[] = [];
        
        for (const session of sessions) {
          try {
            const detailResponse = await fetch(`/api/chat-sessions/${finalUserId}/${session.id}`);
            if (detailResponse.ok) {
              const detailData = await detailResponse.json();
              if (detailData.messages && Array.isArray(detailData.messages)) {
                console.log(`[App] Loaded ${detailData.messages.length} messages from session ${session.id}`);
                detailData.messages.forEach((msg: any) => {
                  allPreviousMessages.push({
                    id: uuidv4(),
                    role: "user",
                    content: msg.user_message,
                  });
                  allPreviousMessages.push({
                    id: uuidv4(),
                    role: "assistant",
                    content: msg.ai_response,
                    sources: msg.message_metadata?.sources || [],
                  });
                });
              }
            }
          } catch (error) {
            console.error(`Failed to load session ${session.id}:`, error);
          }
        }

        // Load the most recent session as the current one
        if (sessions.length > 0) {
          const mostRecentSession = sessions[0];
          setSessionId(mostRecentSession.id);
          console.log("[App] Set current session to:", mostRecentSession.id);
          
          // Filter messages for current session display
          const detailResponse = await fetch(`/api/chat-sessions/${finalUserId}/${mostRecentSession.id}`);
          if (detailResponse.ok) {
            const detailData = await detailResponse.json();
            const currentSessionMessages: Message[] = [];
            if (detailData.messages && Array.isArray(detailData.messages)) {
              detailData.messages.forEach((msg: any) => {
                currentSessionMessages.push({
                  id: uuidv4(),
                  role: "user",
                  content: msg.user_message,
                });
                currentSessionMessages.push({
                  id: uuidv4(),
                  role: "assistant",
                  content: msg.ai_response,
                  sources: msg.message_metadata?.sources || [],
                });
              });
            }
            setMessages(currentSessionMessages);
          }
          
          // Set all previous messages for context in all future requests
          console.log("[App] Total previous messages loaded:", allPreviousMessages.length);
          setAllMessages(allPreviousMessages);
        } else {
          // No previous sessions, create a new one
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          setMessages([]);
          console.log("[App] Created new session:", newSessionId);
          setAllMessages([]);
        }
      } catch (error) {
        console.error("[App] Failed to load sessions:", error);
        // Fallback: create new session
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        setMessages([]);
        setAllMessages([]);
        console.log("[App] Created fallback session:", newSessionId);
      }
    };

    loadUserSessions();
  }, [finalUserId]);

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

    const userMessage = input.trim();
    setInput("");
    setIsLoading(true); // Set loading BEFORE any async operations

    // Check for meeting scheduling intent
    const meetingKeywords = ["schedule", "book", "set meeting", "meeting"];
    const hasMeetingIntent = meetingKeywords.some(keyword =>
      userMessage.toLowerCase().includes(keyword)
    );

    // Try to schedule meeting if intent detected
    if (hasMeetingIntent) {
      try {
        console.log("[Calendar] Attempting to schedule meeting");
        const meetingResponse = await fetch("/api/calendar/schedule-meeting", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: userMessage,
            title: undefined, // Let the backend extract it
          }),
        });

        console.log("[Calendar] Meeting response status:", meetingResponse.status);
        
        if (meetingResponse.ok) {
          const meetingData = await meetingResponse.json();
          console.log("[Calendar] Meeting data:", meetingData);
          
          if (meetingData.success) {
            console.log("[Calendar] Meeting scheduled successfully:", meetingData);
            // Trigger calendar refresh
            setCalendarRefresh(prev => prev + 1);
            setShowCalendar(true); // Auto-show calendar
            
            // Add a notification about the scheduled meeting
            const notificationMsg: Message = {
              id: uuidv4(),
              role: "assistant",
              content: `✅ Meeting Successfully Scheduled!\n\n📅 Title: ${meetingData.title}\n📆 Date: ${new Date(meetingData.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}\n⏰ Time: ${meetingData.time}\n\n✨ The meeting has been added to your Google Calendar and is visible in the calendar view above. Check the calendar on ${meetingData.date} to see your scheduled meeting!`,
            };
            const userMsg: Message = {
              id: uuidv4(),
              role: "user",
              content: userMessage,
            };
            setMessages(prev => [...prev, userMsg, notificationMsg]);
            setAllMessages(prev => [...prev, userMsg, notificationMsg]);
            setIsLoading(false);
            return;
          }
        }
      } catch (error) {
        console.error("Error scheduling meeting:", error);
        // Continue with normal chat if meeting scheduling fails
      }
    }

    // Add user message to UI
    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: userMessage,
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setIsLoading(true);

    try {
      // Build conversation history including ALL previous messages from all sessions
      const conversationHistory = allMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));
      console.log("[Chat] Sending message with:", {
        sessionId,
        finalUserId,
        provider,
        selectedModel,
        conversationHistoryLength: conversationHistory.length,
        currentMessagesLength: messages.length,
        totalMessagesLength: allMessages.length,
      });

      const response = await fetch("/api/backend-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          session_id: sessionId,
          user_id: finalUserId,
          provider: provider,
          model: selectedModel,
          api_key: apiKey,
          document_ids: documentIds,
          url: url || null,
          save_to_db: true,
          conversation_history: conversationHistory,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get response");
      }

      const data = await response.json();
      console.log("[Chat] Response received:", { hasAnswer: !!data.answer, sessionId: data.session_id });

      const assistantMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: data.answer,
        sources: data.sources || [],
      };

      const updatedMessages = [...newMessages, assistantMsg];
      setMessages(updatedMessages);
      // IMPORTANT: Append to allMessages, don't replace it!
      // This ensures we keep context from all previous sessions and messages
      setAllMessages(prev => [...prev, userMsg, assistantMsg]);
    } catch (error) {
      const errorMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `Error: ${error instanceof Error ? error.message : "Failed to get response"}`,
      };
      const updatedMessages = [...newMessages, errorMsg];
      setMessages(updatedMessages);
      // IMPORTANT: Append to allMessages, don't replace it!
      setAllMessages(prev => [...prev, userMsg, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewSession = async () => {
    const newSessionId = uuidv4();
    setSessionId(newSessionId);
    setMessages([]);
    // Keep allMessages to include in context for new sessions
    setShowHistory(false);
  };

  const loadSessionHistory = async (loadSessionId: string, userId: string) => {
    try {
      const response = await fetch(`/api/chat-sessions/${userId}/${loadSessionId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.messages && Array.isArray(data.messages)) {
          const loadedMessages: Message[] = [];
          data.messages.forEach((msg: any) => {
            loadedMessages.push({
              id: uuidv4(),
              role: "user",
              content: msg.user_message,
            });
            loadedMessages.push({
              id: uuidv4(),
              role: "assistant",
              content: msg.ai_response,
              sources: msg.message_metadata?.sources || [],
            });
          });
          setMessages(loadedMessages);
          // Update allMessages to include these messages for future context
          setAllMessages(loadedMessages);
          return true;
        }
      }
    } catch (error) {
      console.error("Failed to load session history:", error);
    }
    return false;
  };

  const handleSessionSelect = async (session: any) => {
    setSessionId(session.id);
    // Load the selected session's messages for display
    const loaded = await loadSessionHistory(session.id, finalUserId);
    
    // Keep allMessages as is (contains all previous context)
    setShowHistory(false);
  };

  return (
    <div className="min-h-screen bg-linear-to-b from-blue-50 to-white">
      <div className="max-w-6xl mx-auto p-4">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-800">Multi-Model Chatbot</h1>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowHistory(!showHistory)}
              variant="outline"
              size="sm"
            >
              <History size={18} className="mr-2" />
              {showHistory ? "Hide" : "History"}
            </Button>

            <Button onClick={handleNewSession} variant="outline" size="sm">
              New Chat
            </Button>

            <Button onClick={onReset} variant="destructive" size="sm">
              <LogOut size={18} className="mr-2" />
              Logout
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chat Area */}
          <div className="lg:col-span-2">
            {/* Chat Messages */}
            <div className="bg-white rounded-lg shadow-md mb-4 h-96 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-500">
                  <div className="text-center">
                    <Bot size={48} className="mx-auto mb-2 opacity-50" />
                    <p>Start a conversation...</p>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={cn(
                        "max-w-2xl px-5 py-3 rounded-lg",
                        msg.role === "user"
                          ? "bg-blue-500 text-white rounded-br-none"
                          : "bg-gray-100 text-gray-900 rounded-bl-none border border-gray-300"
                      )}
                    >
                      <p className="text-base leading-relaxed whitespace-pre-wrap break-words">
                        {msg.content}
                      </p>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 pt-3 border-t border-gray-400 opacity-85">
                          <p className="text-sm font-semibold mb-1">📚 Sources:</p>
                          {msg.sources.map((source, i) => (
                            <p key={i} className="text-sm flex items-start gap-1">
                              <span>📄</span>
                              <span>{source.filename}{source.page ? ` (p. ${source.page})` : ""}</span>
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="space-y-3">
              <ModelSelector
                provider={provider}
                selectedModel={selectedModel}
                onModelChange={setSelectedModel}
                apiKey={apiKey}
              />

              <DocumentUploader onDocumentsSelected={setDocumentIds} />

              <URLInput url={url} onUrlChange={setUrl} />

              <div className="flex gap-2">
                <Textarea
                  ref={textareaRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e as any);
                    }
                  }}
                  placeholder="Ask a question... (Shift+Enter for new line)"
                  className="flex-1 resize-none"
                  disabled={isLoading || !selectedModel}
                />
                <Button
                  type="submit"
                  disabled={isLoading || !selectedModel}
                  className="px-6"
                >
                  {isLoading ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} />
                  )}
                </Button>
              </div>
            </form>
          </div>

          {/* Right Sidebar - Calendar and History */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <CalendarComponent userId={finalUserId} refreshTrigger={calendarRefresh} />
            </div>

            {showHistory && (
              <div className="bg-white rounded-lg shadow-md p-4">
                <ChatHistory
                  userId={finalUserId}
                  currentSessionId={sessionId}
                  onSessionSelect={handleSessionSelect}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
