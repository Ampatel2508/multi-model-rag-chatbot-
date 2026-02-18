"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User, X, Calendar, History, LogOut, Trash2, Download, Menu, FileText, Link as LinkIcon, Settings, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ModelSelector } from "@/components/model-selector";
import { DocumentUploader } from "@/components/document-uploader";
import { URLInput } from "@/components/url-input";
import { ChatHistory } from "@/components/chat-history";
import { CalendarComponent } from "@/components/calendar";
import { type Provider } from "@/lib/providers";
import { cn } from "@/lib/utils";
import { fetchWithRetry } from "@/lib/api-retry";
import { v4 as uuidv4 } from "uuid";
import { signOut } from "next-auth/react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Array<{ filename?: string; page?: number }>;
  timestamp?: string;
}

interface ChatInterfaceProps {
  apiKey: string;
  provider: Provider;
  onReset: () => void;
  userId?: string;
}

interface MeetingData {
  title: string;
  date: string;
  time: string;
  duration_minutes: number;
  participants: string[];
  eventId?: string; // Google Calendar event ID for deletion
}

export function ChatInterface({ apiKey, provider, onReset, userId }: ChatInterfaceProps) {
  // Simple logger utility
  const logger = {
    info: (msg: string) => console.log(`[Chat] ${msg}`),
    error: (msg: string) => console.error(`[Chat] ${msg}`),
    warn: (msg: string) => console.warn(`[Chat] ${msg}`),
  };

  const [selectedModel, setSelectedModel] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [documentIds, setDocumentIds] = useState<string[]>([]);
  const [url, setUrl] = useState("");
  const [sessionId, setSessionId] = useState<string>("");
  const [generatedUserId] = useState<string>(uuidv4());
  const finalUserId = userId || generatedUserId;
  const [allSessions, setAllSessions] = useState<any[]>([]);
  const [allMessages, setAllMessages] = useState<Message[]>([]);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState<MeetingData[]>([]);
  const [meetingIds, setMeetingIds] = useState<string[]>([]);  // Track meeting IDs for deletion
  const [showHistory, setShowHistory] = useState(false);
  const [calendarRefresh, setCalendarRefresh] = useState(0);
  const [meetingScheduled, setMeetingScheduled] = useState(false); // Track if meeting was scheduled in this request
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Load user's sessions on component mount
  useEffect(() => {
    const loadUserSessions = async () => {
      try {
        const response = await fetch(`/api/chat-sessions/${finalUserId}`);
        if (!response.ok) {
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          setMessages([]);
          setAllMessages([]);
          return;
        }
        
        const data = await response.json();
        const sessions = data.sessions || [];
        setAllSessions(sessions);

        let allPreviousMessages: Message[] = [];
        
        for (const session of sessions) {
          try {
            const detailResponse = await fetch(`/api/chat-sessions/${finalUserId}/${session.id}`);
            if (detailResponse.ok) {
              const detailData = await detailResponse.json();
              if (detailData.messages && Array.isArray(detailData.messages)) {
                detailData.messages.forEach((msg: any) => {
                  allPreviousMessages.push({
                    id: uuidv4(),
                    role: "user",
                    content: msg.user_message,
                    timestamp: msg.timestamp
                  });
                  allPreviousMessages.push({
                    id: uuidv4(),
                    role: "assistant",
                    content: msg.ai_response,
                    sources: msg.message_metadata?.sources || [],
                    timestamp: msg.timestamp
                  });
                });
              }
            }
          } catch (error) {
            console.error(`Failed to load session ${session.id}:`, error);
          }
        }

        if (sessions.length > 0) {
          const mostRecentSession = sessions[0];
          setSessionId(mostRecentSession.id);
          
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
                  timestamp: msg.timestamp
                });
                currentSessionMessages.push({
                  id: uuidv4(),
                  role: "assistant",
                  content: msg.ai_response,
                  sources: msg.message_metadata?.sources || [],
                  timestamp: msg.timestamp
                });
              });
            }
            setMessages(currentSessionMessages);
          }
          
          setAllMessages(allPreviousMessages);
        } else {
          const newSessionId = uuidv4();
          setSessionId(newSessionId);
          setMessages([]);
          setAllMessages([]);
        }
      } catch (error) {
        console.error("[App] Failed to load sessions:", error);
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        setMessages([]);
        setAllMessages([]);
      }
    };

    loadUserSessions();
  }, [finalUserId]);

  // Auto-scroll to bottom
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

  // Close menu when clicking outside
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !selectedModel) return;

    const userMessage = input.trim();
    setInput("");

    const userMsg: Message = {
      id: uuidv4(),
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    
    // Check for meeting cancellation commands before processing as regular chat
    const lowerMessage = userMessage.toLowerCase();
    const cancelKeywords = ['cancel', 'delete', 'remove'];
    const hasCancelKeyword = cancelKeywords.some(keyword => lowerMessage.includes(keyword));
    
    if (hasCancelKeyword && lowerMessage.includes('meeting')) {
      // Handle meeting cancellation
      console.log("[Chat] Detected meeting cancellation command");
      
      if (lowerMessage.includes('all')) {
        await handleCancelMeetingsChat("all");
        return;
      } else {
        // Try to extract date/time pattern
        const patterns = ['tomorrow', 'today', 'next', 'yesterday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        const matchedPattern = patterns.find(p => lowerMessage.includes(p));
        if (matchedPattern) {
          await handleCancelMeetingsChat(matchedPattern);
          return;
        } else {
          // Generic cancel message
          await handleCancelMeetingsChat(userMessage);
          return;
        }
      }
    }
    
    setIsLoading(true);

    try {
      // Include all conversation history to preserve context across sessions
      // This ensures the bot can answer questions referencing previous messages
      const conversationHistory = allMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));
      
      logger.info(`[Chat] Sending request with ${conversationHistory.length} messages in conversation history`);
      logger.info(`[Chat] Conversation history: ${JSON.stringify(conversationHistory)}`);

      // Use retry logic for rate limiting tolerance
      const response = await fetchWithRetry("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: finalUserId,
          session_id: sessionId,
          question: userMessage,
          model: selectedModel,
          provider: provider,
          api_key: apiKey,
          document_ids: documentIds.length > 0 ? documentIds : undefined,
          url: url || undefined,
          conversation_history: conversationHistory,
        }),
        maxRetries: 2,
        initialDelay: 1000,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorDetails = null;
        
        try {
          // Try to parse JSON error response
          const parsed = JSON.parse(errorText);
          // FastAPI wraps errors in "detail" field
          if (parsed.detail) {
            errorDetails = parsed.detail;
          } else {
            errorDetails = parsed;
          }
        } catch (e) {
          // If not JSON, use raw text
          errorDetails = errorText;
        }
        
        // If errorDetails is a string, wrap it in Error
        // If it's an object with error field, pass as-is
        const error = new Error(
          typeof errorDetails === "string" 
            ? errorDetails 
            : JSON.stringify(errorDetails)
        );
        throw error;
      }

      const data = await response.json();
      
      // Try to schedule meeting if user mentioned scheduling
      const meetingKeywords = ['schedule', 'meeting', 'book', 'arrange', 'calendar'];
      const hasMeetingKeyword = meetingKeywords.some(keyword => userMessage.toLowerCase().includes(keyword));
      
      // Check if message has actual date/time information
      const dateTimePatterns = [
        /tomorrow|today|tonight|next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/i,
        /\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/i,
        /(?:at|@)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)/i,
        /\d{1,2}:\d{2}\s*(?:am|pm)/i,
      ];
      const hasDateTimeInfo = dateTimePatterns.some(pattern => pattern.test(userMessage));
      
      // Only process meeting if we successfully got LLM response AND user asked for meeting AND has actual date/time details AND not already scheduled
      if (hasMeetingKeyword && hasDateTimeInfo && finalUserId && data.reply && !meetingScheduled) {
        try {
          console.log("[Meeting] Detected meeting intent, attempting to schedule");
          setMeetingScheduled(true); // Mark as scheduled to prevent duplicate
          
          const meetingResponse = await fetch("/api/calendar/schedule-meeting", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              message: userMessage,
              session_id: sessionId || "temp",
              user_id: finalUserId,
            }),
          });
          
          if (meetingResponse.ok) {
            const meetingResult = await meetingResponse.json();
            console.log("[Meeting] Backend response:", meetingResult);
            
            if (!meetingResult.success) {
              console.log("[Meeting] Meeting creation failed:", meetingResult.message);
              // Don't show error if it's a duplicate prevention message
              if (!meetingResult.message.includes("just scheduled")) {
                // Show error message in chat
                const errorMsg: Message = {
                  id: uuidv4(),
                  role: "assistant",
                  content: `❌ ${meetingResult.message}`,
                  timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, errorMsg]);
                setAllMessages(prev => [...prev, errorMsg]);
              }
              // Still refresh calendar even if meeting already exists
              if (setCalendarRefresh) {
                setCalendarRefresh(prev => prev + 1);
              }
              // Add the user message and LLM response
              const userMsg: Message = {
                id: uuidv4(),
                role: "user",
                content: userMessage,
                timestamp: new Date().toISOString()
              };
              const assistantMsg: Message = {
                id: uuidv4(),
                role: "assistant",
                content: data.reply,
                timestamp: new Date().toISOString()
              };
              setMessages(prev => [...prev, userMsg, assistantMsg]);
              setAllMessages(prev => [...prev, userMsg, assistantMsg]);
              setIsLoading(false);
              setMeetingScheduled(false); // Reset flag
              return;
            }
            
            if (meetingResult.success && meetingResult.meeting_data) {
              try {
                // Trigger calendar refresh immediately after successful meeting creation
                if (setCalendarRefresh) {
                  console.log("[Meeting] Triggering calendar refresh");
                  setCalendarRefresh(prev => prev + 1);
                }
                
                // Transform Google Calendar data to MeetingData format
                const googleEvent = meetingResult.meeting_data;
                
                // Parse the datetime from backend - handle both ISO strings and objects
                let displayDate = 'Date';
                let displayTime = 'Time';
                
                if (googleEvent.start) {
                  console.log("[Meeting] Processing time:", googleEvent.start);
                  
                  // Handle both string format (old) and object format (new) from Google Calendar
                  let isoString: string;
                  let timezone = 'Asia/Kolkata';
                  
                  if (typeof googleEvent.start === 'string') {
                    // Old format: just a UTC datetime string
                    isoString = googleEvent.start;
                  } else if (typeof googleEvent.start === 'object' && googleEvent.start.dateTime) {
                    // New format: {dateTime: '...', timeZone: '...'}
                    isoString = googleEvent.start.dateTime;
                    timezone = googleEvent.start.timeZone || 'Asia/Kolkata';
                  } else {
                    isoString = '';
                  }
                  
                  if (isoString) {
                    // Use Intl.DateTimeFormat with the correct timezone to properly format the date
                    const formatter = new Intl.DateTimeFormat('en-US', {
                      timeZone: timezone,
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                      hour12: true
                    });
                    
                    const dateTime = new Date(isoString);
                    const parts = formatter.formatToParts(dateTime);
                    
                    let month = '', day = '', year = '', hour = '', minute = '';
                    
                    parts.forEach(part => {
                      if (part.type === 'month') month = part.value;
                      if (part.type === 'day') day = part.value;
                      if (part.type === 'year') year = part.value;
                      if (part.type === 'hour') hour = part.value;
                      if (part.type === 'minute') minute = part.value;
                    });
                    
                    // Extract AM/PM from formatted string
                    const fullFormatted = formatter.format(dateTime);
                    const amPmMatch = fullFormatted.match(/(AM|PM)/);
                    const amPm = amPmMatch ? amPmMatch[1] : 'AM';
                    
                    displayDate = `${month} ${parseInt(day)}, ${year}`;
                    displayTime = `${parseInt(hour)}:${minute} ${amPm}`;
                    
                    console.log("[Meeting] Formatted date:", displayDate);
                    console.log("[Meeting] Formatted time:", displayTime);
                  }
                }
                
                const transformedEvent: MeetingData = {
                  title: googleEvent.summary || "Meeting",
                  date: displayDate,
                  time: displayTime,
                  duration_minutes: 30, // Default duration shown in UI
                  participants: [], // Can be extracted from event if available
                  eventId: googleEvent.id // Store Google Calendar event ID for deletion
                };
                
                console.log("[Meeting] Data received from backend:", googleEvent);
                console.log("[Meeting] Transformed event:", transformedEvent);
                
                // Update state with new meeting - this triggers instant display
                setCalendarEvents(prev => {
                  const updated = [...prev, transformedEvent];
                  console.log("[Meeting] Updated calendarEvents state:", updated);
                  return updated;
                });
                
                // Refresh calendar to show new event
                setCalendarRefresh(prev => prev + 1);
                // Auto-open calendar to show the scheduled meeting
                setShowCalendar(true);
                setShowHistory(false);
                console.log("[Meeting] ✓ Meeting scheduled successfully:", transformedEvent);
              } catch (transformError) {
                console.error("[Meeting] Error transforming event:", transformError);
                const errorMsg: Message = {
                  id: uuidv4(),
                  role: "assistant",
                  content: `❌ Error processing meeting data. Please try again.`,
                  timestamp: new Date().toISOString()
                };
                setMessages(prev => [...prev, errorMsg]);
                setAllMessages(prev => [...prev, errorMsg]);
              }
            } else {
              console.log("[Meeting] No meeting data received:", meetingResult);
            }
          } else {
            console.log("[Meeting] Meeting API response not OK:", meetingResponse.status);
            const errorMsg: Message = {
              id: uuidv4(),
              role: "assistant",
              content: `❌ Failed to create meeting. API error: ${meetingResponse.status}`,
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMsg]);
            setAllMessages(prev => [...prev, errorMsg]);
          }
        } catch (err) {
          console.log("[Meeting] Could not schedule meeting:", err);
          const errorMsg: Message = {
            id: uuidv4(),
            role: "assistant",
            content: `❌ Error scheduling meeting: ${err instanceof Error ? err.message : 'Unknown error'}`,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, errorMsg]);
          setAllMessages(prev => [...prev, errorMsg]);
        }
      }
      
      // Extract meeting data if present
      if (data.meeting_detected && data.meeting_data) {
        setCalendarEvents([...calendarEvents, data.meeting_data]);
      }

      const assistantMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: data.answer || data.response || "No response received",
        sources: data.sources || [],
        timestamp: new Date().toISOString()
      };

      setMessages([...newMessages, assistantMsg]);
      setAllMessages([...allMessages, userMsg, assistantMsg]);

      // Save this message pair to backend session for history
      try {
        await fetch(`/api/chat-sessions/${finalUserId}/${sessionId}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_message: userMsg.content,
            ai_response: assistantMsg.content,
            provider: provider,
            model: selectedModel,
            sources: assistantMsg.sources || [],
          }),
        });
      } catch (err) {
        console.error("[Chat] Failed to save chat message to backend for history:", err);
      }
    } catch (error) {
      console.error("[Chat] Error:", error);
      
      let errorMsg = "Failed to get response";
      let errorDetails: any = null;
      
      if (error instanceof Error) {
        try {
          // Try to parse the error message as JSON
          const parsed = JSON.parse(error.message);
          
          // Check if it's a dict with "error" field (new format)
          if (typeof parsed === "object" && parsed.error) {
            errorMsg = parsed.error;
            errorDetails = parsed;
          } else if (typeof parsed === "object" && parsed.message) {
            // Fallback to message field
            errorMsg = parsed.message;
            errorDetails = parsed;
          } else if (typeof parsed === "object") {
            // It's an object but no clear error field
            errorMsg = JSON.stringify(parsed);
            errorDetails = parsed;
          } else {
            errorMsg = error.message;
          }
        } catch {
          // Not JSON, use raw message
          errorMsg = error.message;
        }
      }
      
      // Format error message with solutions if available
      let fullErrorMessage = errorMsg;
      if (errorDetails && errorDetails.solutions && Array.isArray(errorDetails.solutions)) {
        fullErrorMessage = `${errorMsg}\n\n📋 Suggested Solutions:\n${errorDetails.solutions.map((s: string, i: number) => `${i + 1}. ${s}`).join("\n")}`;
        
        // Add additional details if available (e.g., when quota is exhausted)
        if (errorDetails.details) {
          fullErrorMessage += `\n\n📊 Details:\n`;
          if (errorDetails.details.issue) {
            fullErrorMessage += `• Issue: ${errorDetails.details.issue}\n`;
          }
          if (errorDetails.details.resets) {
            fullErrorMessage += `• Resets: ${errorDetails.details.resets}\n`;
          }
          if (errorDetails.details.provider) {
            fullErrorMessage += `• Provider: ${errorDetails.details.provider.toUpperCase()}`;
          }
        }
      }
      
      const assistantErrorMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `❌ Error: ${fullErrorMessage}`,
        timestamp: new Date().toISOString()
      };
      setMessages([...newMessages, assistantErrorMsg]);
    } finally {
      setIsLoading(false);
      setMeetingScheduled(false); // Reset meeting flag
    }
  };

  const handleClearChat = async () => {
    if (!messages.length) {
      // No messages to save, just start new session
      const newSessionId = uuidv4();
      setMessages([]);
      setSessionId(newSessionId);
      setAllMessages([]);
      console.log("[Chat] New chat session created:", newSessionId);
      return;
    }
    if (confirm("Are you sure you want to start a new chat? Current chat will be saved to history.")) {
      // Save current chat to backend as a session
      try {
        // Prepare messages for backend
        for (let i = 0; i < messages.length; i += 2) {
          const userMsg = messages[i];
          const aiMsg = messages[i + 1];
          if (userMsg && aiMsg && userMsg.role === "user" && aiMsg.role === "assistant") {
            await fetch(`/api/chat-sessions/${finalUserId}/${sessionId}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                user_message: userMsg.content,
                ai_response: aiMsg.content,
                provider: provider,
                model: selectedModel,
                sources: aiMsg.sources || [],
              }),
            });
          }
        }
      } catch (err) {
        console.error("[Chat] Failed to save old chat session before new chat:", err);
      }
      // Create new session
      const newSessionId = uuidv4();
      setMessages([]);
      setSessionId(newSessionId);
      setAllMessages([]);
      console.log("[Chat] New chat session created:", newSessionId);
    }
  };

  const handleDeleteSession = async (sessionIdToDelete: string) => {
    if (!confirm("Are you sure you want to delete this chat? This action cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`/api/chat-sessions/${finalUserId}/${sessionIdToDelete}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        let errorMsg = "Unknown error";
        try {
          const error = await response.json();
          errorMsg = error.detail || error.message || error.error || "Unknown error";
        } catch (e) {
          // If JSON parsing fails, use status text
          errorMsg = response.statusText || "Failed to delete session";
        }
        alert(`Failed to delete session: ${errorMsg}`);
        return;
      }

      // Remove from local state
      setAllSessions(allSessions.filter(s => s.id !== sessionIdToDelete));
      
      // If deleted session is the current one, create a new session
      if (sessionIdToDelete === sessionId) {
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        setMessages([]);
      }

      console.log("[Chat] Session deleted:", sessionIdToDelete);
      alert("Chat deleted successfully");
    } catch (error) {
      console.error("[Chat] Error deleting session:", error);
      alert("Failed to delete session");
    }
  };

  const handleExportChat = () => {
    const chatData = {
      sessionId,
      messages,
      exportedAt: new Date().toISOString()
    };
    
    const dataStr = JSON.stringify(chatData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat-export-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleLogout = async () => {
    await signOut({ redirect: true, callbackUrl: "/login" });
  };

  const handleLoadSessionFromHistory = async (selectedSession: any) => {
    // Step 1: Save current chat to backend if it has messages
    if (messages.length > 0 && sessionId) {
      try {
        logger.info(`[Chat] Saving current session ${sessionId} before switching`);
        for (let i = 0; i < messages.length; i += 2) {
          const userMsg = messages[i];
          const aiMsg = messages[i + 1];
          if (userMsg && aiMsg && userMsg.role === "user" && aiMsg.role === "assistant") {
            await fetch(`/api/chat-sessions/${finalUserId}/${sessionId}`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                user_message: userMsg.content,
                ai_response: aiMsg.content,
                provider: provider,
                model: selectedModel,
                sources: aiMsg.sources || [],
              }),
            });
          }
        }
        logger.info(`[Chat] Current session saved`);
      } catch (err) {
        logger.error(`[Chat] Failed to save current session before switching: ${err}`);
      }
    }

    // Step 2: Load the old chat's messages
    try {
      logger.info(`[Chat] Loading session ${selectedSession.id}`);
      const response = await fetch(`/api/chat-sessions/${finalUserId}/${selectedSession.id}`);
      if (response.ok) {
        const detailData = await response.json();
        const loadedMessages: Message[] = [];
        
        if (detailData.messages && Array.isArray(detailData.messages)) {
          detailData.messages.forEach((msg: any) => {
            loadedMessages.push({
              id: uuidv4(),
              role: "user",
              content: msg.user_message,
              timestamp: msg.timestamp
            });
            loadedMessages.push({
              id: uuidv4(),
              role: "assistant",
              content: msg.ai_response,
              sources: msg.message_metadata?.sources || [],
              timestamp: msg.timestamp
            });
          });
        }
        
        // Set the loaded messages as both current and all messages (context)
        setMessages(loadedMessages);
        setAllMessages(loadedMessages);
        setSessionId(selectedSession.id);
        setShowHistory(false);
        
        logger.info(`[Chat] Loaded ${loadedMessages.length} messages from session ${selectedSession.id}`);
        logger.info(`[Chat] All messages state updated: ${loadedMessages.length} messages`);
        logger.info(`[Chat] Messages for reference: ${JSON.stringify(loadedMessages)}`);
      } else {
        logger.error(`[Chat] Failed to load session: ${response.status}`);
        alert("Failed to load chat session");
      }
    } catch (err) {
      logger.error(`[Chat] Error loading session: ${err}`);
      alert("Failed to load chat session");
    }
  };

  const handleDeleteMeeting = async (index: number, event: MeetingData) => {
    try {
      console.log(`[Meeting] Deleting meeting at index ${index}:`, event);
      
      // Use eventId if available, otherwise fall back to title+date
      const deleteUrl = event.eventId
        ? `/api/calendar/events/${encodeURIComponent(event.eventId)}`
        : `/api/calendar/events?title=${encodeURIComponent(event.title)}&date=${encodeURIComponent(event.date)}`;
      
      console.log(`[Meeting] Deleting via URL: ${deleteUrl}`);
      
      // Call backend to delete the meeting
      const response = await fetch(deleteUrl, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        console.log(`[Meeting] Meeting deleted successfully`);
        // Remove from state
        setCalendarEvents(prev => {
          const updated = prev.filter((_, i) => i !== index);
          console.log("[Meeting] Updated calendarEvents after deletion:", updated);
          return updated;
        });
        
        // Refresh calendar to sync deletion
        setCalendarRefresh(prev => prev + 1);
        
        // Show success message in chat
        const successMsg: Message = {
          id: uuidv4(),
          role: "assistant",
          content: `✅ Meeting "${event.title}" on ${event.date} has been cancelled.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, successMsg]);
        setAllMessages(prev => [...prev, successMsg]);
      } else {
        console.error(`[Meeting] Failed to delete meeting: ${response.status}`);
        const errorMsg: Message = {
          id: uuidv4(),
          role: "assistant",
          content: `❌ Failed to delete meeting "${event.title}". Please try again.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMsg]);
        setAllMessages(prev => [...prev, errorMsg]);
      }
    } catch (err) {
      console.error("[Meeting] Error deleting meeting:", err);
      const errorMsg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `❌ Error cancelling meeting: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
      setAllMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleCancelMeetingsChat = async (pattern: string) => {
    try {
      console.log(`[Meeting] Processing cancel command: ${pattern}`);
      
      if (pattern === "all") {
        // Cancel all meetings
        if (calendarEvents.length === 0) {
          const msg: Message = {
            id: uuidv4(),
            role: "assistant",
            content: "There are no meetings to cancel.",
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, msg]);
          setAllMessages(prev => [...prev, msg]);
          return;
        }
        
        // Delete all meetings
        for (let i = calendarEvents.length - 1; i >= 0; i--) {
          await handleDeleteMeeting(i, calendarEvents[i]);
        }
        
        const msg: Message = {
          id: uuidv4(),
          role: "assistant",
          content: `✅ All ${calendarEvents.length} meetings have been cancelled.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, msg]);
        setAllMessages(prev => [...prev, msg]);
      } else {
        // Cancel specific meeting by pattern (date or time)
        const matching = calendarEvents.filter(event => 
          event.date.toLowerCase().includes(pattern.toLowerCase()) ||
          event.time.toLowerCase().includes(pattern.toLowerCase())
        );
        
        if (matching.length === 0) {
          const msg: Message = {
            id: uuidv4(),
            role: "assistant",
            content: `No meetings found for "${pattern}".`,
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, msg]);
          setAllMessages(prev => [...prev, msg]);
          return;
        }
        
        // Delete matching meetings
        for (const event of matching) {
          const index = calendarEvents.indexOf(event);
          await handleDeleteMeeting(index, event);
        }
        
        const msg: Message = {
          id: uuidv4(),
          role: "assistant",
          content: `✅ ${matching.length} meeting(s) for "${pattern}" have been cancelled.`,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, msg]);
        setAllMessages(prev => [...prev, msg]);
      }
    } catch (err) {
      console.error("[Meeting] Error in cancel meetings chat:", err);
      const msg: Message = {
        id: uuidv4(),
        role: "assistant",
        content: `❌ Error cancelling meetings: ${err instanceof Error ? err.message : 'Unknown error'}`,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, msg]);
      setAllMessages(prev => [...prev, msg]);
    }
  };

  return (
    <div className="h-screen w-full flex flex-col bg-linear-to-br from-slate-50 to-slate-100 overflow-hidden">
      {/* Top Navigation Bar */}
      <nav className="shrink-0 bg-linear-to-r from-blue-600 to-indigo-600 border-b border-blue-700 shadow-lg">
        <div className="px-6 py-3 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <Bot className="w-6 h-6 text-blue-600" />
            </div>
            <h1 className="text-xl font-bold text-white">Multi-Model Chatbot</h1>
          </div>

          {/* Navbar Items */}
          <div className="flex items-center gap-1">
            {/* Model Selector */}
            <div className="flex items-center gap-2 px-3 py-2 bg-white bg-opacity-10 rounded-lg hover:bg-opacity-20 transition-colors">
              <Settings className="w-4 h-4 text-white" />
              <div className="w-48">
                <ModelSelector
                  provider={provider}
                  apiKey={apiKey}
                  selectedModel={selectedModel}
                  onModelChange={setSelectedModel}
                />
              </div>
            </div>

            {/* Documents Button */}
            <button
              onClick={() => {
                setShowHistory(false);
                setShowCalendar(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-white bg-opacity-10 hover:bg-opacity-20 rounded-lg transition-colors text-white font-medium"
              title="Upload Documents"
            >
              <FileText className="w-4 h-4" />
              <span className="text-sm">Documents</span>
              {documentIds.length > 0 && (
                <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">{documentIds.length}</span>
              )}
            </button>

            {/* URL Input Button */}
            <button
              onClick={() => {
                setShowHistory(false);
                setShowCalendar(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-white bg-opacity-10 hover:bg-opacity-20 rounded-lg transition-colors text-white font-medium"
              title="Add URL"
            >
              <LinkIcon className="w-4 h-4" />
              <span className="text-sm">URL</span>
              {url && <span className="bg-green-500 text-white text-xs px-2 py-0.5 rounded-full ml-1">✓</span>}
            </button>

            {/* Calendar Events */}
            <button
              onClick={() => {
                setShowCalendar(!showCalendar);
                setShowHistory(false);
              }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors font-medium ${
                showCalendar
                  ? 'bg-white bg-opacity-30 text-white'
                  : 'bg-white bg-opacity-10 hover:bg-opacity-20 text-white'
              }`}
              title="Calendar Events"
            >
              <Calendar className="w-4 h-4" />
              <span className="text-sm">Events</span>
              {calendarEvents.length > 0 && (
                <span className="bg-yellow-400 text-blue-600 text-xs px-2 py-0.5 rounded-full ml-1 font-bold">{calendarEvents.length}</span>
              )}
            </button>

            {/* Chat History */}
            <button
              onClick={() => {
                setShowHistory(!showHistory);
                setShowCalendar(false);
              }}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors font-medium ${
                showHistory
                  ? 'bg-white bg-opacity-30 text-white'
                  : 'bg-white bg-opacity-10 hover:bg-opacity-20 text-white'
              }`}
              title="Chat History"
            >
              <History className="w-4 h-4" />
              <span className="text-sm">History</span>
              {allSessions.length > 0 && (
                <span className="bg-purple-400 text-white text-xs px-2 py-0.5 rounded-full ml-1 font-bold">{allSessions.length}</span>
              )}
            </button>

            {/* New Chat Button */}
            <button
              onClick={handleClearChat}
              className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 rounded-lg transition-colors text-white font-semibold"
              title="Start a new chat (current chat will be saved to history)"
            >
              <Plus className="w-4 h-4" />
              <span className="text-sm">New Chat</span>
            </button>

            {/* Export Chat */}
            <button
              onClick={handleExportChat}
              className="flex items-center gap-2 px-3 py-2 bg-green-500 bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-colors text-white font-medium"
              title="Export Chat"
            >
              <Download className="w-4 h-4" />
              <span className="text-sm">Export</span>
            </button>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 bg-orange-500 bg-opacity-20 hover:bg-opacity-30 rounded-lg transition-colors text-white font-medium ml-2"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
              <span className="text-sm">Logout</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Secondary Toolbar - Documents and URLs */}
      <div className="shrink-0 bg-white border-b border-slate-200 shadow-sm px-6 py-3 flex items-center gap-4">
        {/* Document Uploader */}
        <div className="flex-1 max-w-sm">
          <label className="text-xs font-semibold text-slate-600 block mb-2">Upload Documents</label>
          <DocumentUploader onDocumentsSelected={setDocumentIds} />
        </div>

        {/* URL Input */}
        <div className="flex-1 max-w-sm">
          <label className="text-xs font-semibold text-slate-600 block mb-2">Crawl URL</label>
          <URLInput url={url} onUrlChange={setUrl} />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center max-w-md">
                  <div className="w-16 h-16 bg-linear-to-br from-blue-100 to-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Bot className="w-8 h-8 text-blue-600" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-800 mb-2">Welcome!</h2>
                  <p className="text-slate-600 mb-6">
                    Start a conversation. I can help with various tasks including:
                  </p>
                  <ul className="text-left text-sm text-slate-600 space-y-2 mb-6">
                    <li>✓ Answering questions across multiple AI models</li>
                    <li>✓ Processing documents and analyzing their content</li>
                    <li>✓ Crawling web URLs for information</li>
                    <li>✓ Scheduling meetings to your Google Calendar</li>
                    <li>✓ Maintaining conversation context across sessions</li>
                  </ul>
                  {!selectedModel && (
                    <p className="text-sm text-orange-600 font-medium">👉 Select a model from the menu to begin</p>
                  )}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3 animate-fadeIn",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "assistant" && (
                    <div className="w-8 h-8 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                  
                  <div
                    className={cn(
                      "max-w-3xl rounded-lg px-5 py-4 wrap-break-word",
                      message.role === "assistant"
                        ? "bg-white text-slate-900 shadow-md border border-slate-300"
                        : "bg-linear-to-r from-blue-600 to-indigo-600 text-white"
                    )}
                  >
                    <p className="text-base leading-relaxed whitespace-pre-wrap break-words">{message.content}</p>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-opacity-30 border-current">
                        <p className="text-sm font-semibold opacity-80 mb-2">📚 Sources:</p>
                        <ul className="text-sm space-y-1.5 opacity-85">
                          {message.sources.map((source, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-lg">📄</span>
                              <span>{source.filename}{source.page && ` (Page ${source.page})`}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {message.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center shrink-0">
                      <User className="w-5 h-5 text-slate-700" />
                    </div>
                  )}
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="flex gap-3 animate-fadeIn">
                <div className="w-8 h-8 rounded-full bg-linear-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white text-slate-800 shadow-sm border border-slate-200 rounded-lg px-4 py-3">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="shrink-0 border-t border-slate-200 bg-white px-6 py-4 shadow-lg">
            <form onSubmit={handleSubmit} className="space-y-3">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message here... (or describe a meeting to schedule)"
                className="w-full resize-none bg-slate-50 border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e as any);
                  }
                }}
              />
              
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs text-slate-500">
                  Shift + Enter for new line
                </div>
                <Button
                  type="submit"
                  disabled={isLoading || !selectedModel}
                  className="bg-linear-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-6 py-2 rounded-lg flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Thinking...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      Send
                    </>
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>

        {/* Side Panel for Calendar and History */}
        {(showCalendar || showHistory) && (
          <div className="w-80 border-l border-slate-200 bg-white shadow-lg flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-linear-to-r from-blue-50 to-indigo-50">
              <h3 className="text-lg font-bold text-slate-800">
                {showCalendar ? "📅 Scheduled Meetings" : "📜 Chat History"}
              </h3>
              <button
                onClick={() => {
                  setShowCalendar(false);
                  setShowHistory(false);
                }}
                className="p-1 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-slate-600" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {showCalendar && (
                <div className="p-4 space-y-4">
                  {/* Google Calendar Component */}
                  <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                    <div className="bg-blue-50 border-b border-slate-200 p-3">
                      <p className="text-sm font-semibold text-slate-700">📅 Your Google Calendar</p>
                    </div>
                    <CalendarComponent userId={finalUserId} refreshTrigger={calendarRefresh} />
                  </div>

                  {/* Scheduled Meetings Section */}
                  <div>
                    <p className="text-sm font-semibold text-slate-700 mb-2">📌 Meetings Scheduled in Chat</p>
                    {calendarEvents.length === 0 ? (
                      <p className="text-sm text-slate-500 text-center py-4 bg-slate-50 rounded-lg">
                        No meetings scheduled yet. Mention a meeting in your message to schedule one!
                      </p>
                    ) : (
                      <div className="space-y-3">
                        {calendarEvents.map((event, i) => (
                          <div
                            key={i}
                            className="p-3 bg-linear-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg hover:shadow-md transition-shadow group relative"
                          >
                            <div className="flex justify-between items-start gap-3">
                              <div className="flex-1">
                                <h4 className="font-semibold text-slate-800 text-sm mb-1">
                                  {event.title}
                                </h4>
                                <div className="text-xs text-slate-600 space-y-1">
                                  <p>📅 {event.date}</p>
                                  <p>⏰ {event.time}</p>
                                  <p>⏳ {event.duration_minutes} minutes</p>
                                  {event.participants.length > 0 && (
                                    <p>👥 {event.participants.join(", ")}</p>
                                  )}
                                </div>
                              </div>
                              <button
                                onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  handleDeleteMeeting(i, event);
                                }}
                                className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors shrink-0"
                                title="Delete meeting"
                              >
                                <Trash2 size={18} />
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {showHistory && (
                <ChatHistory
                  userId={finalUserId}
                  currentSessionId={sessionId}
                  onSessionSelect={handleLoadSessionFromHistory}
                />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
