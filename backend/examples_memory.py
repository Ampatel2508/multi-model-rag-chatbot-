"""
Example: How to use Chat Memory with the API

This shows how to use the chat history and memory management features.
"""

import requests
import json

API_URL = "http://localhost:8000"
SESSION_ID = "test-session-123"

# Example API key (replace with your actual key)
API_KEY = "your-api-key-here"


def example_chat_with_memory():
    """Example: Chat with memory persistence."""
    
    print("=" * 70)
    print("CHAT WITH MEMORY EXAMPLE")
    print("=" * 70)
    
    # First message
    print("\n[1] First Message:")
    question1 = "What is the capital of France?"
    
    chat_request1 = {
        "question": question1,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "api_key": API_KEY,
        "document_ids": [],
        "url": None,
        "session_id": SESSION_ID
    }
    
    response1 = requests.post(f"{API_URL}/api/chat", json=chat_request1)
    print(f"Question: {question1}")
    print(f"Answer: {response1.json()['answer']}")
    
    # Second message - memory will have context from first message
    print("\n[2] Second Message (with memory context):")
    question2 = "What is its population?"
    
    chat_request2 = {
        "question": question2,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "api_key": API_KEY,
        "document_ids": [],
        "url": None,
        "session_id": SESSION_ID  # Same session = memory is retained
    }
    
    response2 = requests.post(f"{API_URL}/api/chat", json=chat_request2)
    print(f"Question: {question2}")
    print(f"Answer: {response2.json()['answer']}")
    print("(The AI understands you're asking about France from previous message)")
    
    # View chat history
    print("\n[3] View Chat History:")
    history_response = requests.get(f"{API_URL}/api/memory/history/{SESSION_ID}")
    history_data = history_response.json()
    
    print(f"Session: {history_data['session_id']}")
    print(f"Message Count: {history_data['summary']['message_count']}")
    print(f"\nFull History:")
    print(history_data['history'])
    
    # Export session
    print("\n[4] Export Session as JSON:")
    export_response = requests.post(f"{API_URL}/api/memory/export/{SESSION_ID}")
    exported = export_response.json()['data']
    print(json.dumps(exported, indent=2))
    
    # Get summary
    print("\n[5] Get Session Summary:")
    summary_response = requests.get(f"{API_URL}/api/memory/summary/{SESSION_ID}")
    summary = summary_response.json()['summary']
    print(f"Session ID: {summary['session_id']}")
    print(f"Messages: {summary['message_count']}")
    print(f"Preview: {summary['preview']}")
    
    # Clear session
    print("\n[6] Clear Session Memory:")
    clear_response = requests.delete(f"{API_URL}/api/memory/clear/{SESSION_ID}")
    print(clear_response.json()['message'])


def example_multiple_sessions():
    """Example: Different sessions have isolated memories."""
    
    print("\n" + "=" * 70)
    print("MULTIPLE SESSIONS EXAMPLE")
    print("=" * 70)
    
    session1 = "user-alice-session"
    session2 = "user-bob-session"
    
    # Alice's conversation
    print(f"\n[Alice - Session: {session1}]")
    alice_q = "What is Python?"
    alice_req = {
        "question": alice_q,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "api_key": API_KEY,
        "document_ids": [],
        "url": None,
        "session_id": session1
    }
    alice_resp = requests.post(f"{API_URL}/api/chat", json=alice_req)
    print(f"Question: {alice_q}")
    
    # Bob's conversation
    print(f"\n[Bob - Session: {session2}]")
    bob_q = "What is JavaScript?"
    bob_req = {
        "question": bob_q,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "api_key": API_KEY,
        "document_ids": [],
        "url": None,
        "session_id": session2
    }
    bob_resp = requests.post(f"{API_URL}/api/chat", json=bob_req)
    print(f"Question: {bob_q}")
    
    # Each session has its own memory
    print(f"\nAlice's memory (sessions isolated):")
    alice_hist = requests.get(f"{API_URL}/api/memory/history/{session1}").json()
    print(f"  Messages: {alice_hist['summary']['message_count']}")
    
    print(f"\nBob's memory (sessions isolated):")
    bob_hist = requests.get(f"{API_URL}/api/memory/history/{session2}").json()
    print(f"  Messages: {bob_hist['summary']['message_count']}")


if __name__ == "__main__":
    print("Chat Memory API Examples\n")
    print("NOTE: Make sure your backend is running on http://localhost:8000")
    print("NOTE: Replace 'your-api-key-here' with a real API key\n")
    
    try:
        # Uncomment to run examples
        # example_chat_with_memory()
        # example_multiple_sessions()
        
        print("Examples are ready! Uncomment them in the script to run.")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the backend is running!")
