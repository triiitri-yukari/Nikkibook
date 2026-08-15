"""
Database module for NikkiBook.
Handles SQLite connection, schema creation, and migrations.
Uses parameterized queries throughout for security.
"""
import sqlite3
from contextlib import contextmanager
from typing import Generator, Any
from .config import DB_PATH

# Current schema version - increment when making schema changes
SCHEMA_VERSION = 1


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database connections.
    Ensures connections are properly closed and changes are committed.
    
    Usage:
        with get_connection() as conn:
            cursor = conn.execute("SELECT * FROM images")
    """
    conn = sqlite3.connect(str(DB_PATH))
    # Enable foreign keys (disabled by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    # Return rows as sqlite3.Row objects for dict-like access
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Get the current schema version from the database."""
    try:
        cursor = conn.execute("SELECT version FROM schema_version ORDER BY version DESC LIMIT 1")
        row = cursor.fetchone()
        return row["version"] if row else 0
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0


def init_database() -> None:
    """
    Initialize the database with required tables.
    Creates tables on first run and applies migrations for upgrades.
    """
    with get_connection() as conn:
        current_version = get_schema_version(conn)
        
        if current_version < 1:
            _apply_migration_v1(conn)
        
        # Add future migrations here:
        # if current_version < 2:
        #     _apply_migration_v2(conn)


def _apply_migration_v1(conn: sqlite3.Connection) -> None:
    """
    Initial schema creation (Version 1).
    Creates all base tables for the application.
    """
    # Schema version tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    
    # Categories table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
    """)
    
    # Subcategories table (belongs to a category)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subcategories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            UNIQUE(category_id, name)
        )
    """)
    
    # Images table (main data)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id TEXT PRIMARY KEY,
            name TEXT,
            filename TEXT NOT NULL,
            original_filename TEXT,
            category_id TEXT NOT NULL,
            subcategory_id TEXT,
            share_string TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE SET NULL
        )
    """)
    
    # Indexes for common queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_images_category ON images(category_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_images_subcategory ON images(subcategory_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_images_created ON images(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_subcategories_category ON subcategories(category_id)")
    
    # Record that we've applied version 1
    conn.execute("INSERT INTO schema_version (version) VALUES (?)", (1,))


# ============================================================================
# Category Operations (CRUD with parameterized queries)
# ============================================================================

def create_category(category_id: str, name: str, created_at: str) -> None:
    """Insert a new category into the database."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO categories (id, name, created_at) VALUES (?, ?, ?)",
            (category_id, name, created_at)
        )


def get_all_categories() -> list[dict[str, Any]]:
    """Retrieve all categories ordered by name."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM categories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def update_category(category_id: str, name: str) -> None:
    """Update a category's name."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE categories SET name = ? WHERE id = ?",
            (name, category_id)
        )


def delete_category(category_id: str) -> None:
    """Delete a category and all its subcategories/images (via CASCADE)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))


# ============================================================================
# Subcategory Operations
# ============================================================================

def create_subcategory(subcategory_id: str, name: str, category_id: str, created_at: str) -> None:
    """Insert a new subcategory under a category."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO subcategories (id, name, category_id, created_at) VALUES (?, ?, ?, ?)",
            (subcategory_id, name, category_id, created_at)
        )


def get_subcategories_for_category(category_id: str) -> list[dict[str, Any]]:
    """Retrieve all subcategories for a given category."""
    with get_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM subcategories WHERE category_id = ? ORDER BY name",
            (category_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_all_subcategories() -> list[dict[str, Any]]:
    """Retrieve all subcategories."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM subcategories ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]


def update_subcategory(subcategory_id: str, name: str) -> None:
    """Update a subcategory's name."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE subcategories SET name = ? WHERE id = ?",
            (name, subcategory_id)
        )


def delete_subcategory(subcategory_id: str) -> None:
    """Delete a subcategory (images will have subcategory_id set to NULL)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM subcategories WHERE id = ?", (subcategory_id,))


# ============================================================================
# Image Operations
# ============================================================================

def create_image(
    image_id: str,
    name: str | None,
    filename: str,
    original_filename: str | None,
    category_id: str,
    subcategory_id: str | None,
    share_string: str,
    created_at: str
) -> None:
    """Insert a new image record."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO images 
               (id, name, filename, original_filename, category_id, subcategory_id, share_string, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (image_id, name, filename, original_filename, category_id, subcategory_id, share_string, created_at)
        )


def get_all_images() -> list[dict[str, Any]]:
    """Retrieve all images with category and subcategory names."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT i.*, c.name as category_name, s.name as subcategory_name
            FROM images i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN subcategories s ON i.subcategory_id = s.id
            ORDER BY i.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_images_by_category(category_id: str, subcategory_id: str | None = None) -> list[dict[str, Any]]:
    """Retrieve images filtered by category and optionally subcategory."""
    with get_connection() as conn:
        if subcategory_id == "__none__":
            cursor = conn.execute("""
                SELECT i.*, c.name as category_name, s.name as subcategory_name
                FROM images i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN subcategories s ON i.subcategory_id = s.id
                WHERE i.category_id = ? AND i.subcategory_id IS NULL
                ORDER BY i.created_at DESC
            """, (category_id,))
        elif subcategory_id:
            cursor = conn.execute("""
                SELECT i.*, c.name as category_name, s.name as subcategory_name
                FROM images i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN subcategories s ON i.subcategory_id = s.id
                WHERE i.category_id = ? AND i.subcategory_id = ?
                ORDER BY i.created_at DESC
            """, (category_id, subcategory_id))
        else:
            cursor = conn.execute("""
                SELECT i.*, c.name as category_name, s.name as subcategory_name
                FROM images i
                LEFT JOIN categories c ON i.category_id = c.id
                LEFT JOIN subcategories s ON i.subcategory_id = s.id
                WHERE i.category_id = ?
                ORDER BY i.created_at DESC
            """, (category_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_image_by_id(image_id: str) -> dict[str, Any] | None:
    """Retrieve a single image by its ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT i.*, c.name as category_name, s.name as subcategory_name
            FROM images i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN subcategories s ON i.subcategory_id = s.id
            WHERE i.id = ?
        """, (image_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_image(
    image_id: str,
    name: str | None = None,
    category_id: str | None = None,
    subcategory_id: str | None = None,
    share_string: str | None = None
) -> None:
    """Update an image's metadata. Only updates provided fields."""
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
    if subcategory_id is not None:
        updates.append("subcategory_id = ?")
        params.append(subcategory_id if subcategory_id else None)
    if share_string is not None:
        updates.append("share_string = ?")
        params.append(share_string)
    
    if updates:
        params.append(image_id)
        with get_connection() as conn:
            conn.execute(
                f"UPDATE images SET {', '.join(updates)} WHERE id = ?",
                params
            )


def delete_image(image_id: str) -> str | None:
    """Delete an image record and return the filename for file cleanup."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT filename FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        if row:
            filename = row["filename"]
            conn.execute("DELETE FROM images WHERE id = ?", (image_id,))
            return filename
        return None


def search_images(query: str) -> list[dict[str, Any]]:
    """
    Search images by name, category name, subcategory name, or share_string.
    Uses LIKE for partial matching.
    """
    search_term = f"%{query}%"
    with get_connection() as conn:
        cursor = conn.execute("""
            SELECT i.*, c.name as category_name, s.name as subcategory_name
            FROM images i
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN subcategories s ON i.subcategory_id = s.id
            WHERE i.name LIKE ?
               OR i.original_filename LIKE ?
               OR c.name LIKE ?
               OR s.name LIKE ?
               OR i.share_string LIKE ?
            ORDER BY i.created_at DESC
        """, (search_term, search_term, search_term, search_term, search_term))
        return [dict(row) for row in cursor.fetchall()]
