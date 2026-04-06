"""
Data models for NikkiBook.
Uses dataclasses for clean, typed data structures.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Category:
    """Represents a top-level category for organizing images."""
    id: str
    name: str
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        """Create a Category from a database row dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        )


@dataclass
class Subcategory:
    """Represents a subcategory within a parent category."""
    id: str
    name: str
    category_id: str
    created_at: datetime
    
    @classmethod
    def from_dict(cls, data: dict) -> "Subcategory":
        """Create a Subcategory from a database row dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            category_id=data["category_id"],
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"]
        )


@dataclass
class ImageRecord:
    """
    Represents an image in the catalog.
    
    Attributes:
        id: Unique identifier (UUID)
        name: Optional display name
        filename: UUID-based filename stored in images/ directory
        original_filename: Original filename when imported
        category_id: Parent category ID (required)
        subcategory_id: Optional subcategory ID
        share_string: URL or text for sharing (validated: empty or http(s)://)
        created_at: When the image was added
        category_name: Joined from categories table (for display)
        subcategory_name: Joined from subcategories table (for display)
    """
    id: str
    filename: str
    category_id: str
    created_at: datetime
    name: Optional[str] = None
    original_filename: Optional[str] = None
    subcategory_id: Optional[str] = None
    share_string: str = ""
    # These are populated from JOINs, not stored in images table
    category_name: Optional[str] = field(default=None, repr=False)
    subcategory_name: Optional[str] = field(default=None, repr=False)
    
    @classmethod
    def from_dict(cls, data: dict) -> "ImageRecord":
        """Create an ImageRecord from a database row dictionary."""
        return cls(
            id=data["id"],
            name=data.get("name"),
            filename=data["filename"],
            original_filename=data.get("original_filename"),
            category_id=data["category_id"],
            subcategory_id=data.get("subcategory_id"),
            share_string=data.get("share_string", ""),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
            category_name=data.get("category_name"),
            subcategory_name=data.get("subcategory_name")
        )
    
    @property
    def display_name(self) -> str:
        """Get the best available name for display."""
        if self.name:
            return self.name
        if self.original_filename:
            return self.original_filename
        return self.filename
