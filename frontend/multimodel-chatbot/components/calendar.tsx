"use client";

import { useState, useEffect } from "react";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight, X, Trash2 } from "lucide-react";

interface CalendarEvent {
  id: string;
  summary: string;
  start: string;
  end: string;
  description?: string;
  eventType?: string;
  canDelete?: boolean;
  htmlLink?: string;
}

interface CalendarComponentProps {
  userId?: string;
  refreshTrigger?: number;
}

export function CalendarComponent({ userId, refreshTrigger = 0 }: CalendarComponentProps) {
  const [events, setEvents] = useState<{ [key: string]: CalendarEvent[] }>({});
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMonthEvents();
  }, [currentMonth, refreshTrigger]); // Re-load when refreshTrigger changes

  const loadMonthEvents = async () => {
    setLoading(true);
    try {
      const year = currentMonth.getFullYear();
      const month = currentMonth.getMonth();
      const startDate = new Date(year, month, 1).toISOString().split("T")[0];
      const endDate = new Date(year, month + 1, 0).toISOString().split("T")[0];

      console.log(`[Calendar] Loading events for ${startDate} to ${endDate}`);
      
      const response = await fetch(
        `/api/calendar/events?start_date=${startDate}&end_date=${endDate}&max_results=50`
      );
      
      console.log(`[Calendar] API response status: ${response.status}`);
      
      if (response.ok) {
        const data = await response.json();
        console.log(`[Calendar] Data received:`, data);
        
        if (data.events && Array.isArray(data.events)) {
          const grouped: { [key: string]: CalendarEvent[] } = {};
          data.events.forEach((event: CalendarEvent) => {
            const date = event.start.split("T")[0];
            if (!grouped[date]) {
              grouped[date] = [];
            }
            grouped[date].push(event);
          });
          console.log(`[Calendar] Grouped events:`, grouped);
          setEvents(grouped);
        } else {
          console.log("[Calendar] No events array in response");
          setEvents({});
        }
      } else {
        console.warn(`[Calendar] API returned status ${response.status}`);
        console.warn("[Calendar] Calendar API not available yet. Make sure backend is running and authorized.");
        setEvents({});
      }
    } catch (error) {
      console.error("[Calendar] Failed to load calendar events:", error);
      console.error("[Calendar] This is normal if backend isn't running or not authorized yet");
      setEvents({});
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const monthName = currentMonth.toLocaleString("default", {
    month: "long",
    year: "numeric",
  });

  const daysInMonth = getDaysInMonth(currentMonth);
  const firstDay = getFirstDayOfMonth(currentMonth);
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  
  const previousMonthDays = getDaysInMonth(
    new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1)
  );
  
  const previousMonthFillDays = Array.from({ length: firstDay }, (_, i) =>
    previousMonthDays - firstDay + i + 1
  );

  const allDays = [...previousMonthFillDays, ...days];
  const nextMonthFillDays = Array.from(
    { length: (42 - allDays.length) % 7 || 0 },
    (_, i) => i + 1
  );
  const calendarDays = [...allDays, ...nextMonthFillDays];

  const previousMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1)
    );
  };

  const nextMonth = () => {
    setCurrentMonth(
      new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1)
    );
  };

  const handleDateClick = (day: number) => {
    // Use local date format to avoid timezone offset issues
    const year = currentMonth.getFullYear();
    const month = String(currentMonth.getMonth() + 1).padStart(2, '0');
    const dayStr = String(day).padStart(2, '0');
    const dateStr = `${year}-${month}-${dayStr}`;
    console.log(`[Calendar] Date clicked: ${dateStr}`);
    setSelectedDate(dateStr);
  };

  const getDateForDay = (dayIndex: number) => {
    let year, month, day;
    
    if (dayIndex < firstDay) {
      const prevMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1);
      year = prevMonth.getFullYear();
      month = prevMonth.getMonth();
      day = previousMonthDays - firstDay + dayIndex + 1;
    } else if (dayIndex < firstDay + daysInMonth) {
      year = currentMonth.getFullYear();
      month = currentMonth.getMonth();
      day = dayIndex - firstDay + 1;
    } else {
      const nextMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1);
      year = nextMonth.getFullYear();
      month = nextMonth.getMonth();
      day = dayIndex - firstDay - daysInMonth + 1;
    }
    
    // Use local date format without timezone conversion
    const monthStr = String(month + 1).padStart(2, '0');
    const dayStr = String(day).padStart(2, '0');
    const dateStr = `${year}-${monthStr}-${dayStr}`;
    return dateStr;
  };

  const selectedDateEvents = selectedDate ? events[selectedDate] || [] : [];

  const handleClearAllMeetings = async () => {
    if (!selectedDate || selectedDateEvents.length === 0) {
      return;
    }

    const confirmClear = window.confirm(
      `Are you sure you want to delete all ${selectedDateEvents.length} meeting(s) on this date? This action cannot be undone.`
    );

    if (!confirmClear) {
      return;
    }

    try {
      console.log(`[Calendar] Deleting all ${selectedDateEvents.length} meetings for ${selectedDate}`);
      
      let deletedCount = 0;
      let failedCount = 0;

      // Delete each meeting one by one
      for (const event of selectedDateEvents) {
        if (event.canDelete === false) {
          console.log(`[Calendar] Skipping non-deletable event: ${event.summary}`);
          failedCount++;
          continue;
        }

        try {
          const response = await fetch(`/api/calendar/events/${encodeURIComponent(event.id)}`, {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
            },
          });

          if (response.ok) {
            deletedCount++;
            console.log(`[Calendar] Successfully deleted: ${event.summary}`);
          } else {
            failedCount++;
            console.error(`[Calendar] Failed to delete: ${event.summary}`);
          }
        } catch (error) {
          failedCount++;
          console.error(`[Calendar] Error deleting ${event.summary}:`, error);
        }
      }

      // Update UI
      setEvents((prevEvents) => {
        const updatedEvents = { ...prevEvents };
        delete updatedEvents[selectedDate];
        return updatedEvents;
      });

      setSelectedDate("");
      
      // Reload events
      await loadMonthEvents();

      // Show result message
      if (failedCount > 0) {
        alert(`Cleared ${deletedCount} meeting(s). ${failedCount} meeting(s) could not be deleted (non-deletable event types).`);
      } else {
        alert(`All ${deletedCount} meeting(s) have been deleted successfully!`);
      }
    } catch (error) {
      console.error("[Calendar] Error clearing all meetings:", error);
      alert("Failed to clear all meetings. Please try again.");
    }
  };

  const handleDeleteEvent = async (eventId: string, eventTitle: string, canDelete: boolean = true) => {
    if (!canDelete) {
      alert("This event type cannot be deleted. It is managed by Google Calendar.");
      return;
    }

    if (!window.confirm(`Are you sure you want to delete "${eventTitle}"?`)) {
      return;
    }

    try {
      console.log(`[Calendar] Deleting event: ${eventId}`);
      
      const response = await fetch(`/api/calendar/events/${encodeURIComponent(eventId)}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log(`[Calendar] Delete response status: ${response.status}`);
      
      let responseData = null;
      try {
        const text = await response.text();
        console.log(`[Calendar] Response body: ${text}`);
        if (text) {
          responseData = JSON.parse(text);
        }
      } catch (e) {
        console.log(`[Calendar] Could not parse response body:`, e);
      }
      
      if (response.ok) {
        console.log(`[Calendar] Event ${eventId} deleted successfully`);
        
        // Immediately update the local state to remove the event
        setEvents((prevEvents) => {
          const updatedEvents = { ...prevEvents };
          
          // Remove the event from all dates
          Object.keys(updatedEvents).forEach((dateStr) => {
            updatedEvents[dateStr] = updatedEvents[dateStr].filter(
              (event) => event.id !== eventId
            );
            
            // Remove the date entry if no events left
            if (updatedEvents[dateStr].length === 0) {
              delete updatedEvents[dateStr];
            }
          });
          
          // If the deleted event was selected and was the last one, clear selection
          if (selectedDate && (!updatedEvents[selectedDate] || updatedEvents[selectedDate].length === 0)) {
            setSelectedDate("");
          }
          
          console.log(`[Calendar] Updated events after deletion:`, updatedEvents);
          return updatedEvents;
        });
        
        // Reload the month events to ensure sync with backend
        console.log(`[Calendar] Reloading events from backend`);
        loadMonthEvents();
        
        alert("Meeting deleted successfully!");
      } else {
        const errorDetail = responseData?.detail || responseData?.error || `HTTP ${response.status}`;
        console.error(`[Calendar] Failed to delete event:`, errorDetail);
        console.error(`[Calendar] Full response:`, responseData);
        
        // Show specific error messages based on error type
        if (response.status === 400) {
          alert(`Cannot delete this meeting:\n\n${errorDetail}`);
        } else if (response.status === 404) {
          console.warn(`[Calendar] Event not found - it may have been deleted already`);
          alert("Meeting already deleted or not found.\n\nReloading calendar...");
          // Remove event from state and reload
          setEvents((prevEvents) => {
            const updatedEvents = { ...prevEvents };
            Object.keys(updatedEvents).forEach((dateStr) => {
              updatedEvents[dateStr] = updatedEvents[dateStr].filter(
                (event) => event.id !== eventId
              );
              if (updatedEvents[dateStr].length === 0) {
                delete updatedEvents[dateStr];
              }
            });
            return updatedEvents;
          });
          setTimeout(() => loadMonthEvents(), 500);
        } else {
          alert(`Failed to delete meeting: ${errorDetail}`);
        }
      }
    } catch (error) {
      console.error("[Calendar] Error deleting event:", error);
      alert("Error deleting meeting. Please try again.");
    }
  };

  return (
    <div className="w-full h-full flex flex-col bg-white rounded-lg">
      <div className="flex items-center justify-between p-4 border-b border-slate-200">
        <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
          <CalendarIcon className="w-5 h-5" />
          Calendar
        </h3>
        {loading && <div className="text-xs text-slate-500">Loading...</div>}
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={previousMonth}
              className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ChevronLeft className="w-5 h-5 text-slate-600" />
            </button>
            <h4 className="text-sm font-semibold text-slate-700">{monthName}</h4>
            <button
              onClick={nextMonth}
              className="p-1 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ChevronRight className="w-5 h-5 text-slate-600" />
            </button>
          </div>

          <div className="grid grid-cols-7 gap-1 mb-4">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
              <div
                key={day}
                className="text-center text-xs font-semibold text-slate-600 py-2"
              >
                {day}
              </div>
            ))}
            {calendarDays.map((_, dayIndex) => {
              const day = calendarDays[dayIndex];
              const dateStr = getDateForDay(dayIndex);
              const isCurrentMonth = dayIndex >= firstDay && dayIndex < firstDay + daysInMonth;
              const hasEvents = events[dateStr]?.length > 0;
              const isSelected = selectedDate === dateStr;
              const isToday = dateStr === new Date().toISOString().split("T")[0];

              return (
                <div
                  key={dayIndex}
                  onClick={() => isCurrentMonth && handleDateClick(day)}
                  className={`p-2 text-center text-sm rounded-lg min-h-20 border cursor-pointer transition-colors relative ${
                    isSelected
                      ? "bg-blue-100 border-blue-400"
                      : isToday
                      ? "bg-yellow-50 border-yellow-200"
                      : hasEvents && isCurrentMonth
                      ? "bg-green-50 border-green-200"
                      : isCurrentMonth
                      ? "bg-white border-slate-200 hover:bg-slate-50"
                      : "text-slate-300 bg-slate-50 border-slate-100"
                  }`}
                >
                  <div className={`font-semibold ${isCurrentMonth ? "text-slate-700" : "text-slate-400"}`}>
                    {day}
                  </div>
                  {hasEvents && isCurrentMonth && (
                    <div className="mt-1 space-y-0.5">
                      {events[dateStr].slice(0, 1).map((event, idx) => (
                        <div
                          key={idx}
                          className="text-xs bg-green-200 text-green-800 rounded px-0.5 truncate"
                          title={event.summary}
                        >
                          {event.summary}
                        </div>
                      ))}
                      {events[dateStr].length > 1 && (
                        <div className="text-xs text-green-700 font-semibold">
                          +{events[dateStr].length - 1}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

          </div>
        </div>

        {events && Object.keys(events).length > 0 ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h5 className="text-sm font-semibold text-slate-700">
                {selectedDate
                  ? `Events on ${new Date(selectedDate).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                    })}`
                  : "Upcoming Events"}
              </h5>
              {selectedDate && selectedDateEvents.length > 0 && (
                <button
                  onClick={handleClearAllMeetings}
                  className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1"
                  title="Delete all meetings for this date"
                >
                  <Trash2 className="w-3 h-3" />
                  Clear All
                </button>
              )}
            </div>

            {selectedDateEvents.length > 0 ? (
              selectedDateEvents.map((event) => (
                <div
                  key={event.id}
                  className="p-3 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg hover:shadow-md transition-shadow flex justify-between items-start"
                >
                  <div className="flex-1">
                    <p className="font-semibold text-slate-800 text-sm mb-1">
                      {event.summary}
                    </p>
                    <div className="text-xs text-slate-600 space-y-1">
                      <p>
                        ⏰{" "}
                        {new Date(event.start).toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}{" "}
                        -{" "}
                        {new Date(event.end).toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                      {event.description && <p>📝 {event.description}</p>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleDeleteEvent(event.id, event.summary, event.canDelete !== false)}
                    className={`ml-2 p-1 rounded transition-colors flex-shrink-0 ${
                      event.canDelete !== false
                        ? "text-red-500 hover:bg-red-100 cursor-pointer" 
                        : "text-gray-400 cursor-not-allowed"
                    }`}
                    title={event.canDelete !== false ? "Delete meeting" : "Cannot delete this event type"}
                    disabled={event.canDelete === false}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : selectedDate ? (
              <div className="text-center py-4 text-sm text-slate-500">
                No meetings scheduled for this date
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-slate-500">
                Select a date to view events
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8 flex flex-col items-center gap-3">
            <p className="text-sm text-slate-500">No events scheduled</p>
            <p className="text-xs text-slate-400">
              💡 Make sure backend is running and authorized to see meetings
            </p>
          </div>
        )}
        
        {/* Status Message */}
        <div className="mt-auto pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-600">
            ✓ Calendar Interface Ready
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Schedule a meeting to get started
          </p>
        </div>
      </div>
    </div>
  );
}
