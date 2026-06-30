"""
Database operations for the Bookmark Manager
Uses SQLite for persistence with JSON for tag storage
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from models import Bookmark


class Database:
    """Handles all database operations for bookmarks"""

    def __init__(self, db_path: str = "bookmarks.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    tags_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_archived INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.commit()

    def _execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()

    def _row_to_bookmark(self, row: tuple) -> Bookmark:
        """Convert database row to Bookmark object"""
        return Bookmark(
            id=row[0],
            url=row[1],
            title=row[2],
            description=row[3],
            tags=json.loads(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
            is_archived=bool(row[7])
        )

    def add_bookmark(self, bookmark: Bookmark) -> Bookmark:
        """Add a new bookmark to the database"""
        query = """
            INSERT INTO bookmarks 
            (url, title, description, tags_json, created_at, updated_at, is_archived)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        bookmark.created_at = datetime.now()
        bookmark.updated_at = datetime.now()
        
        params = (
            bookmark.url,
            bookmark.title,
            bookmark.description,
            json.dumps(bookmark.tags),
            bookmark.created_at.isoformat(),
            bookmark.updated_at.isoformat(),
            int(bookmark.is_archived)
        )
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            bookmark.id = cursor.lastrowid
        
        return bookmark

    def get_all_bookmarks(self, include_archived: bool = False) -> List[Bookmark]:
        """Get all bookmarks, optionally excluding archived ones"""
        query = "SELECT * FROM bookmarks"
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY updated_at DESC"
        
        rows = self._execute_query(query)
        return [self._row_to_bookmark(row) for row in rows]

    def get_bookmark_by_id(self, bookmark_id: int) -> Optional[Bookmark]:
        """Get a bookmark by its ID"""
        query = "SELECT * FROM bookmarks WHERE id = ?"
        rows = self._execute_query(query, (bookmark_id,))
        
        if rows:
            return self._row_to_bookmark(rows[0])
        return None

    def get_bookmarks_by_tag(self, tag: str, include_archived: bool = False) -> List[Bookmark]:
        """Get all bookmarks with a specific tag"""
        # SQLite doesn't have native JSON search, so we'll do it in Python
        all_bookmarks = self.get_all_bookmarks(include_archived)
        return [b for b in all_bookmarks if tag in b.tags]

    def get_bookmarks_by_url(self, url: str) -> List[Bookmark]:
        """Search bookmarks by URL (partial match)"""
        query = "SELECT * FROM bookmarks WHERE url LIKE ? ORDER BY updated_at DESC"
        rows = self._execute_query(query, (f"%{url}%",))
        return [self._row_to_bookmark(row) for row in rows]

    def get_bookmarks_by_title(self, title: str) -> List[Bookmark]:
        """Search bookmarks by title (partial match)"""
        query = "SELECT * FROM bookmarks WHERE title LIKE ? ORDER BY updated_at DESC"
        rows = self._execute_query(query, (f"%{title}%",))
        return [self._row_to_bookmark(row) for row in rows]

    def search_bookmarks(self, query: str) -> List[Bookmark]:
        """Search bookmarks by URL, title, description, or tags"""
        all_bookmarks = self.get_all_bookmarks(include_archived=True)
        query_lower = query.lower()
        
        results = []
        for bookmark in all_bookmarks:
            if (query_lower in bookmark.url.lower() or
                query_lower in bookmark.title.lower() or
                (bookmark.description and query_lower in bookmark.description.lower()) or
                any(query_lower in tag.lower() for tag in bookmark.tags)):
                results.append(bookmark)
        
        return results

    def update_bookmark(self, bookmark: Bookmark) -> Bookmark:
        """Update an existing bookmark"""
        bookmark.updated_at = datetime.now()
        
        query = """
            UPDATE bookmarks 
            SET url = ?, title = ?, description = ?, tags_json = ?, 
                updated_at = ?, is_archived = ?
            WHERE id = ?
        """
        
        params = (
            bookmark.url,
            bookmark.title,
            bookmark.description,
            json.dumps(bookmark.tags),
            bookmark.updated_at.isoformat(),
            int(bookmark.is_archived),
            bookmark.id
        )
        
        self._execute_query(query, params)
        return bookmark

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Delete a bookmark by ID"""
        query = "DELETE FROM bookmarks WHERE id = ?"
        rows_affected = self._execute_query(query, (bookmark_id,))
        return len(rows_affected) > 0

    def archive_bookmark(self, bookmark_id: int) -> Optional[Bookmark]:
        """Archive a bookmark (soft delete)"""
        bookmark = self.get_bookmark_by_id(bookmark_id)
        if bookmark:
            bookmark.is_archived = True
            return self.update_bookmark(bookmark)
        return None

    def unarchive_bookmark(self, bookmark_id: int) -> Optional[Bookmark]:
        """Unarchive a bookmark"""
        bookmark = self.get_bookmark_by_id(bookmark_id)
        if bookmark:
            bookmark.is_archived = False
            return self.update_bookmark(bookmark)
        return None

    def get_all_tags(self) -> List[str]:
        """Get all unique tags from all bookmarks"""
        bookmarks = self.get_all_bookmarks(include_archived=True)
        tags = set()
        for bookmark in bookmarks:
            tags.update(bookmark.tags)
        return sorted(list(tags))

    def get_bookmark_count(self) -> Dict[str, int]:
        """Get statistics about bookmarks"""
        all_bookmarks = self.get_all_bookmarks(include_archived=True)
        active = sum(1 for b in all_bookmarks if not b.is_archived)
        archived = len(all_bookmarks) - active
        
        return {
            'total': len(all_bookmarks),
            'active': active,
            'archived': archived
        }

    def clear_all_bookmarks(self) -> int:
        """Clear all bookmarks (dangerous operation)"""
        query = "DELETE FROM bookmarks"
        rows = self._execute_query(query)
        return len(rows) if rows else 0

    def export_to_json(self) -> List[dict]:
        """Export all bookmarks as JSON"""
        bookmarks = self.get_all_bookmarks(include_archived=True)
        return [b.to_dict() for b in bookmarks]

    def import_from_json(self, data: List[dict]) -> int:
        """Import bookmarks from JSON data"""
        imported = 0
        for item in data:
            try:
                bookmark = Bookmark.from_dict(item)
                # Check if URL already exists
                existing = self.get_bookmarks_by_url(bookmark.url)
                if not existing:
                    # Reset ID to let DB auto-generate
                    bookmark.id = None
                    self.add_bookmark(bookmark)
                    imported += 1
            except Exception as e:
                print(f"Error importing bookmark: {e}")
                continue
        return imported
