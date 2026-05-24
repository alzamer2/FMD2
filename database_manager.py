"""
Database Manager
Replaces: FavoritesDB.pas, DownloadsDB.pas, SQLiteDataModules.pas
Handles: SQLite operations for favorites, downloads, history
"""
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages SQLite database operations.
    In Pascal: Uses TSQLiteQuery, TSQLiteConnection.
    In Python: Uses built-in sqlite3 module.
    """
    
    def __init__(self, db_path: str = "fmd.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()

    def _connect(self) -> None:
        """Establish database connection."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(self.db_path))
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info(f"Database connected: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def _create_tables(self) -> None:
        """Create database schema if not exists."""
        cursor = self.conn.cursor()
        
        # Favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                manga_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                cover_url TEXT,
                author TEXT,
                artist TEXT,
                genres TEXT,
                status TEXT,
                last_chapter TEXT,
                last_chapter_date TIMESTAMP,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(website, manga_id)
            )
        ''')
        
        # Downloads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                manga_id TEXT NOT NULL,
                title TEXT NOT NULL,
                chapter_id TEXT NOT NULL,
                chapter_name TEXT,
                chapter_number REAL,
                pages_count INTEGER DEFAULT 0,
                downloaded_pages INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending', -- pending, downloading, completed, failed
                save_path TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_completed TIMESTAMP,
                UNIQUE(website, manga_id, chapter_id)
            )
        ''')
        
        # History table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website TEXT NOT NULL,
                manga_id TEXT NOT NULL,
                title TEXT,
                chapter_id TEXT,
                chapter_name TEXT,
                page_number INTEGER DEFAULT 1,
                date_read TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorites_website ON favorites(website)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_date ON history(date_read)')
        
        self.conn.commit()
        logger.info("Database tables created/verified")

    # ========== Favorites Operations ==========
    
    def add_favorite(self, website: str, manga_id: str, title: str, **kwargs) -> bool:
        """Add or update a favorite manga."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO favorites (website, manga_id, title, url, cover_url, author, artist, genres, status, last_chapter, last_chapter_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(website, manga_id) DO UPDATE SET
                    title = excluded.title,
                    url = excluded.url,
                    cover_url = excluded.cover_url,
                    author = excluded.author,
                    artist = excluded.artist,
                    genres = excluded.genres,
                    status = excluded.status,
                    last_chapter = excluded.last_chapter,
                    last_chapter_date = excluded.last_chapter_date
            ''', (
                website, manga_id, title,
                kwargs.get('url'), kwargs.get('cover_url'),
                kwargs.get('author'), kwargs.get('artist'),
                kwargs.get('genres'), kwargs.get('status'),
                kwargs.get('last_chapter'), kwargs.get('last_chapter_date')
            ))
            self.conn.commit()
            logger.debug(f"Favorite added/updated: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to add favorite: {e}")
            return False

    def get_favorites(self, website: Optional[str] = None) -> List[Dict]:
        """Get all favorites, optionally filtered by website."""
        try:
            cursor = self.conn.cursor()
            if website:
                cursor.execute('SELECT * FROM favorites WHERE website = ? ORDER BY title', (website,))
            else:
                cursor.execute('SELECT * FROM favorites ORDER BY title')
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get favorites: {e}")
            return []

    def remove_favorite(self, website: str, manga_id: str) -> bool:
        """Remove a favorite."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM favorites WHERE website = ? AND manga_id = ?', (website, manga_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to remove favorite: {e}")
            return False

    # ========== Downloads Operations ==========
    
    def add_download(self, website: str, manga_id: str, title: str, 
                     chapter_id: str, chapter_name: str, **kwargs) -> bool:
        """Add a chapter to download queue."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO downloads 
                (website, manga_id, title, chapter_id, chapter_name, chapter_number, 
                 pages_count, status, save_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                website, manga_id, title, chapter_id, chapter_name,
                kwargs.get('chapter_number', 0),
                kwargs.get('pages_count', 0),
                kwargs.get('status', 'pending'),
                kwargs.get('save_path')
            ))
            self.conn.commit()
            logger.debug(f"Download added: {title} - {chapter_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add download: {e}")
            return False

    def get_downloads(self, status: Optional[str] = None) -> List[Dict]:
        """Get downloads, optionally filtered by status."""
        try:
            cursor = self.conn.cursor()
            if status:
                cursor.execute('SELECT * FROM downloads WHERE status = ? ORDER BY date_added', (status,))
            else:
                cursor.execute('SELECT * FROM downloads ORDER BY date_added DESC')
            
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get downloads: {e}")
            return []

    def update_download_status(self, website: str, manga_id: str, chapter_id: str, 
                               status: str, **kwargs) -> bool:
        """Update download status and progress."""
        try:
            cursor = self.conn.cursor()
            
            updates = []
            values = []
            
            updates.append("status = ?")
            values.append(status)
            
            if 'downloaded_pages' in kwargs:
                updates.append("downloaded_pages = ?")
                values.append(kwargs['downloaded_pages'])
            
            if 'save_path' in kwargs:
                updates.append("save_path = ?")
                values.append(kwargs['save_path'])
            
            if status == 'completed':
                updates.append("date_completed = ?")
                values.append(datetime.now())
            
            values.extend([website, manga_id, chapter_id])
            
            query = f"UPDATE downloads SET {', '.join(updates)} WHERE website = ? AND manga_id = ? AND chapter_id = ?"
            cursor.execute(query, values)
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to update download status: {e}")
            return False

    # ========== History Operations ==========
    
    def add_history(self, website: str, manga_id: str, title: str,
                   chapter_id: str, chapter_name: str, page_number: int = 1) -> bool:
        """Add reading history."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO history (website, manga_id, title, chapter_id, chapter_name, page_number)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (website, manga_id, title, chapter_id, chapter_name, page_number))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to add history: {e}")
            return False

    def get_recent_history(self, limit: int = 50) -> List[Dict]:
        """Get recent reading history."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM history 
                ORDER BY date_read DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# Global instance singleton
_db_instance: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        from config_manager import get_config
        config = get_config()
        db_path = config.get("database", "path", "./data/fmd.db")
        _db_instance = DatabaseManager(db_path)
    return _db_instance

if __name__ == "__main__":
    # Test the DatabaseManager
    logging.basicConfig(level=logging.INFO)
    
    db = DatabaseManager("test_fmd.db")
    
    # Test adding favorite
    success = db.add_favorite(
        website="mangadex",
        manga_id="12345",
        title="Test Manga",
        url="https://example.com/manga/12345",
        author="Test Author",
        genres="Action,Adventure"
    )
    assert success, "Failed to add favorite"
    
    # Test getting favorites
    favs = db.get_favorites()
    assert len(favs) == 1, f"Expected 1 favorite, got {len(favs)}"
    assert favs[0]['title'] == "Test Manga"
    
    # Test adding download
    success = db.add_download(
        website="mangadex",
        manga_id="12345",
        title="Test Manga",
        chapter_id="ch-001",
        chapter_name="Chapter 1",
        chapter_number=1.0,
        pages_count=20
    )
    assert success, "Failed to add download"
    
    # Test updating download
    success = db.update_download_status(
        website="mangadex",
        manga_id="12345",
        chapter_id="ch-001",
        status="downloading",
        downloaded_pages=5
    )
    assert success, "Failed to update download"
    
    # Test getting downloads
    downloads = db.get_downloads()
    assert len(downloads) == 1, f"Expected 1 download, got {len(downloads)}"
    assert downloads[0]['downloaded_pages'] == 5
    
    # Test history
    success = db.add_history(
        website="mangadex",
        manga_id="12345",
        title="Test Manga",
        chapter_id="ch-001",
        chapter_name="Chapter 1",
        page_number=5
    )
    assert success, "Failed to add history"
    
    history = db.get_recent_history()
    assert len(history) == 1, f"Expected 1 history entry, got {len(history)}"
    
    print("✅ DatabaseManager tests passed!")
    
    # Cleanup
    db.close()
    Path("test_fmd.db").unlink()
