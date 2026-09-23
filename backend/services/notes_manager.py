import sqlite3
import time
from typing import List, Dict, Any, Optional
from backend.config import settings

class NotesManager:
    """Manages voice dictations, quick notes, and reminders in a local SQLite database."""

    def __init__(self, db_path=None):
        self.db_path = str(db_path or settings.DB_PATH)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if not already present."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def add_note(self, content: str, title: Optional[str] = None, category: str = "voice_dictation") -> Dict[str, Any]:
        """Create a new note from spoken dictation or text input."""
        cleaned_content = content.strip()
        if not cleaned_content:
            return {"success": False, "error": "Note content cannot be empty."}

        # Auto-generate title if none provided
        if not title:
            words = cleaned_content.split()
            title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
            if not title:
                title = f"Note {time.strftime('%Y-%m-%d %H:%M')}"

        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (title, content, category) VALUES (?, ?, ?)",
                (title, cleaned_content, category)
            )
            note_id = cursor.lastrowid
            conn.commit()

        return {
            "success": True,
            "id": note_id,
            "title": title,
            "content": cleaned_content,
            "category": category,
            "message": f"Note '{title}' saved successfully."
        }

    def list_notes(self, search: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve notes with optional keyword filtering."""
        with self._get_connection() as conn:
            if search:
                pattern = f"%{search}%"
                cursor = conn.execute(
                    "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT ?",
                    (pattern, pattern, limit)
                )
            else:
                cursor = conn.execute("SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def delete_note(self, note_id: int) -> Dict[str, Any]:
        """Delete note by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
            if cursor.rowcount > 0:
                return {"success": True, "message": f"Note #{note_id} deleted."}
            return {"success": False, "error": f"Note #{note_id} not found."}

    def export_all_notes(self) -> str:
        """Export all notes formatted in Markdown."""
        notes = self.list_notes(limit=500)
        output = ["# SUVI Voice Intelligence Notes Export\n"]
        for n in notes:
            output.append(f"## {n['title']} (ID: {n['id']})")
            output.append(f"*Created: {n['created_at']} | Category: {n['category']}*\n")
            output.append(f"{n['content']}\n")
            output.append("---\n")
        return "\n".join(output)

notes_manager = NotesManager()
