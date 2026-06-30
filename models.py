"""
Data models for the Bookmark Manager
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import json


@dataclass
class Bookmark:
    """Bookmark model representing a saved URL"""
    id: Optional[int]
    url: str
    title: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    is_archived: bool = False

    def to_dict(self) -> dict:
        """Convert bookmark to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_archived': self.is_archived
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Bookmark':
        """Create bookmark from dictionary"""
        return cls(
            id=data['id'],
            url=data['url'],
            title=data['title'],
            description=data.get('description'),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            is_archived=data.get('is_archived', False)
        )

    def __str__(self) -> str:
        """String representation of bookmark"""
        tags_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        archived_str = " [ARCHIVED]" if self.is_archived else ""
        return f"{self.title}{archived_str}{tags_str}\n  {self.url}"
