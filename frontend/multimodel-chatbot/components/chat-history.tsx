"use client";

import React, { useState, useEffect } from "react";
import { Trash2, MessageSquare, ChevronDown, Search } from "lucide-react";

interface ChatMessage {
  id: string;
  userMessage: string;
  aiResponse: string;
  provider?: string;
  model?: string;
  createdAt: Date;
}

interface ChatSession {
  id: string;
  sessionName: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  messages?: ChatMessage[];
}

interface ChatHistoryProps {
  userId?: string;
  onSessionSelect?: (session: ChatSession) => void;
  currentSessionId?: string;
}

export function ChatHistory({
  userId,
  onSessionSelect,
  currentSessionId,
}: ChatHistoryProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [expandedSessionId, setExpandedSessionId] = useState<string | null>(null);

  useEffect(() => {
    if (userId) {
      fetchSessions();
    }
  }, [userId]);

  const fetchSessions = async () => {
    if (!userId) {
      console.warn("[ChatHistory] userId is not set");
      return;
    }

    try {
      setLoading(true);
      console.log("[ChatHistory] Fetching sessions for userId:", userId);
      
      const response = await fetch(`/api/chat-sessions/${userId}`);
      console.log("[ChatHistory] Response status:", response.status);

      if (!response.ok) {
        console.error(`[ChatHistory] Failed to fetch sessions: ${response.status}`);
        const errorText = await response.text();
        console.error("[ChatHistory] Error response:", errorText);
        setLoading(false);
        return;
      }

      const data = await response.json();
      console.log("[ChatHistory] Sessions data:", data);
      
      const processedSessions: ChatSession[] = (data.sessions || []).map(
        (s: any) => ({
          id: s.id,
          sessionName: s.session_name,
          createdAt: new Date(s.created_at),
          updatedAt: new Date(s.updated_at),
          messageCount: s.message_count,
        })
      );
      console.log("[ChatHistory] Processed sessions:", processedSessions);
      setSessions(processedSessions);

      // Select current session if provided
      if (currentSessionId) {
        const current = processedSessions.find((s) => s.id === currentSessionId);
        if (current) {
          setSelectedSession(current);
        }
      }
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSessionDetails = async (sessionId: string) => {
    if (!userId) return;

    try {
      const response = await fetch(`/api/chat-sessions/${userId}/${sessionId}`);

      if (response.ok) {
        const data = await response.json();
        const session: ChatSession = {
          id: data.id,
          sessionName: data.session_name,
          createdAt: new Date(data.created_at),
          updatedAt: new Date(data.updated_at),
          messageCount: data.message_count,
          messages: data.messages.map((m: any) => ({
            id: m.id,
            userMessage: m.user_message,
            aiResponse: m.ai_response,
            provider: m.provider,
            model: m.model,
            createdAt: new Date(m.created_at),
          })),
        };

        setSelectedSession(session);
        onSessionSelect?.(session);
      }
    } catch (error) {
      console.error("Failed to fetch session details:", error);
    }
  };

  const handleSessionClick = (session: ChatSession) => {
    setExpandedSessionId(
      expandedSessionId === session.id ? null : session.id
    );
    fetchSessionDetails(session.id);
  };

  const handleDeleteSession = async (
    e: React.MouseEvent,
    sessionId: string
  ) => {
    e.stopPropagation();

    if (!confirm("Delete this chat session? This action cannot be undone.")) return;

    try {
      const response = await fetch(`/api/chat-sessions/${userId}/${sessionId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setSessions(sessions.filter((s) => s.id !== sessionId));
        if (selectedSession?.id === sessionId) {
          setSelectedSession(null);
        }
        console.log("[ChatHistory] Session deleted successfully");
        // Refresh sessions list
        await fetchSessions();
      } else {
        let errorMsg = "Unknown error";
        try {
          const error = await response.json();
          errorMsg = error.detail || error.message || error.error || "Unknown error";
        } catch (e) {
          // If JSON parsing fails, use status text
          errorMsg = response.statusText || "Failed to delete session";
        }
        alert(`Failed to delete session: ${errorMsg}`);
      }
    } catch (error) {
      console.error("[ChatHistory] Failed to delete session:", error);
      alert("Failed to delete session. Please try again.");
    }
  };

  const handleRenameSession = async (
    sessionId: string,
    newName: string
  ) => {
    if (!newName.trim()) return;

    try {
      const response = await fetch(`/api/chat-sessions/${sessionId}/name`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_name: newName }),
      });

      if (response.ok) {
        setSessions(
          sessions.map((s) =>
            s.id === sessionId ? { ...s, sessionName: newName } : s
          )
        );
        if (selectedSession?.id === sessionId) {
          setSelectedSession({ ...selectedSession, sessionName: newName });
        }
      }
    } catch (error) {
      console.error("Failed to rename session:", error);
    }
  };

  const filteredSessions = sessions.filter((session) =>
    session.sessionName.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full max-w-2xl mx-auto p-4 bg-white rounded-lg shadow-md">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <MessageSquare size={24} />
          Chat History
        </h2>

        {/* Search */}
        <div className="relative">
          <Search size={18} className="absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search sessions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Sessions List */}
      <div className="space-y-2 max-h-96 overflow-y-auto">
        {filteredSessions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            {sessions.length === 0
              ? "No chat sessions yet. Start a new conversation!"
              : "No sessions match your search."}
          </div>
        ) : (
          filteredSessions.map((session) => (
            <div
              key={session.id}
              className={`border rounded-lg transition-all ${
                selectedSession?.id === session.id
                  ? "bg-blue-50 border-blue-400"
                  : "bg-white border-gray-300 hover:bg-gray-50"
              }`}
            >
              {/* Session Header */}
              <div
                onClick={() => handleSessionClick(session)}
                className="p-4 cursor-pointer flex items-center justify-between"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-800 truncate">
                    {session.sessionName}
                  </div>
                  <div className="text-sm text-gray-500">
                    {session.messageCount} messages • Updated{" "}
                    {session.updatedAt.toLocaleDateString()}
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <ChevronDown
                    size={20}
                    className={`text-gray-400 transition-transform ${
                      expandedSessionId === session.id ? "rotate-180" : ""
                    }`}
                  />

                  <button
                    onClick={(e) => handleDeleteSession(e, session.id)}
                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Delete session"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              {/* Session Messages */}
              {expandedSessionId === session.id && selectedSession?.messages && (
                <div className="border-t border-gray-300 p-4 bg-gray-50 space-y-3 max-h-80 overflow-y-auto">
                  {selectedSession.messages.length === 0 ? (
                    <div className="text-gray-500 text-sm">No messages yet</div>
                  ) : (
                    selectedSession.messages.map((message) => (
                      <div key={message.id} className="space-y-2">
                        {/* User Message */}
                        <div className="flex justify-end">
                          <div className="max-w-xs bg-blue-500 text-white p-3 rounded-lg rounded-tr-none">
                            <p className="text-sm">{message.userMessage}</p>
                          </div>
                        </div>

                        {/* AI Response */}
                        <div className="flex justify-start">
                          <div className="max-w-xs bg-gray-300 text-gray-800 p-3 rounded-lg rounded-tl-none">
                            <p className="text-sm line-clamp-3">
                              {message.aiResponse}
                            </p>
                            {message.provider && (
                              <div className="text-xs text-gray-600 mt-1">
                                {message.provider} • {message.model}
                              </div>
                            )}
                            <div className="text-xs text-gray-500 mt-1">
                              {message.createdAt.toLocaleTimeString()}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {loading && (
        <div className="text-center py-4 text-gray-500">Loading...</div>
      )}
    </div>
  );
}
