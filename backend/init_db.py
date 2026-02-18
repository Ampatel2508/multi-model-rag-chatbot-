#!/usr/bin/env python3
"""
Database initialization script for Multi-Model Chatbot
Run this script to set up the PostgreSQL database and tables
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent))

def init_database():
    """Initialize the database with all required tables."""
    try:
        print("=" * 70)
        print("Multi-Model Chatbot - Database Initialization")
        print("=" * 70)
        
        # Import after path is set
        from app.database import init_db, engine
        from app.config import settings
        
        print(f"\n[*] Database URL: {settings.DATABASE_URL}")
        print("[*] Initializing database...")
        
        print("\n[*] Creating database tables...")
        init_db()
        print("[✓] Database tables created successfully!")
        
        print("\n[*] Creating indexes...")
        with engine.connect() as conn:
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_user_id ON calendar_events(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time);",
                "CREATE INDEX IF NOT EXISTS idx_calendar_settings_user_id ON calendar_settings(user_id);",
            ]
            
            for index_sql in indexes:
                try:
                    conn.execute(index_sql)
                except Exception as e:
                    if "already exists" not in str(e):
                        print(f"[!] Warning creating index: {e}")
            
            conn.commit()
        
        print("[✓] Indexes created!")
        
        print("\n" + "=" * 70)
        print("✓ Database initialization complete!")
        print("=" * 70)
        print("\nYou can now start the application with:")
        print("  python run.py")
        print("  or")
        print("  uvicorn app.main:app --reload")
        print("\nAPI will be available at: http://localhost:8000")
        print("API Docs at: http://localhost:8000/docs")
        
        return True
        
    except Exception as e:
        print(f"\n[✗] Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False


def reset_database():
    """Reset the database (delete all data and recreate tables)."""
    try:
        print("\n" + "=" * 70)
        print("WARNING: This will delete ALL data in the database!")
        print("=" * 70)
        
        response = input("\nAre you sure you want to continue? (type 'yes' to confirm): ")
        
        if response.lower() != "yes":
            print("Reset cancelled.")
            return False
        
        from app.database import drop_all_tables, init_db
        
        print("\n[*] Dropping all tables...")
        drop_all_tables()
        print("[✓] All tables dropped!")
        
        print("\n[*] Recreating tables...")
        init_db()
        print("[✓] Tables recreated!")
        
        print("\n[✓] Database reset complete!")
        return True
        
    except Exception as e:
        print(f"\n[✗] Error resetting database: {e}")
        return False


def show_stats():
    """Show database statistics."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        print("\n" + "=" * 70)
        print("Database Statistics")
        print("=" * 70)
        
        with engine.connect() as conn:
            tables = [
                "users",
                "chat_sessions",
                "chat_messages",
                "calendar_settings",
                "calendar_events"
            ]
            
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                    count = result.scalar()
                    print(f"{table:20s}: {count:>6,} records")
                except Exception as e:
                    print(f"{table:20s}: Error - {e}")
        
        print("=" * 70)
        
    except Exception as e:
        print(f"Error getting database stats: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "reset":
            reset_database()
        elif command == "stats":
            show_stats()
        elif command == "init":
            init_database()
        else:
            print(f"Unknown command: {command}")
            print("\nUsage:")
            print("  python init_db.py          # Initialize database")
            print("  python init_db.py reset    # Reset database (delete all data)")
            print("  python init_db.py stats    # Show database statistics")
    else:
        # Default: initialize
        success = init_database()
        sys.exit(0 if success else 1)
