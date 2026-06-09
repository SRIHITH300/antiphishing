"""
Hash-based URL lookup service
Fast path for known URLs using SHA-256 hashing
"""
import sqlite3
from typing import Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HashLookup:
    """
    Fast hash-based lookup for known URLs
    Returns cached results immediately without ML inference
    """
    
    def __init__(self, db_path: str = "phishing_detection.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create hash lookup table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS url_hashes (
                    hash TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    is_phishing BOOLEAN NOT NULL,
                    confidence REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for fast lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_hash ON url_hashes(hash)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
            # Seed known URLs if available
            try:
                from pathlib import Path
                seed_path = Path(__file__).resolve().parents[3] / "database" / "seed_hashes.sql"
                if seed_path.exists():
                    with open(seed_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()
                    cursor.executescript(sql_script)
                    conn.commit()
                    logger.info("Seeded url_hashes from seed_hashes.sql")
            except Exception as se:
                logger.warning(f"Seeding skipped: {se}")
            finally:
                conn.close()
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def lookup(self, url_hash: str) -> Optional[Dict]:
        """
        Lookup URL by hash
        
        Args:
            url_hash: SHA-256 hash of normalized URL
            
        Returns:
            Dictionary with result or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT url, is_phishing, confidence
                FROM url_hashes
                WHERE hash = ?
            """, (url_hash,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                val = result[1]
                is_phish = False
                try:
                    # Normalize common representations to boolean
                    if isinstance(val, (int, float)):
                        is_phish = int(val) == 1
                    elif isinstance(val, bytes):
                        s = val.decode('utf-8', errors='ignore').strip().lower()
                        is_phish = s in ('1', 'true', 't', 'yes', 'y')
                    elif isinstance(val, str):
                        s = val.strip().lower()
                        is_phish = s in ('1', 'true', 't', 'yes', 'y')
                except Exception:
                    is_phish = False
                return {
                    'url': result[0],
                    'is_phishing': is_phish,
                    'confidence': result[2],
                    'source': 'cache'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Hash lookup failed: {e}")
            return None
    
    def store(self, url_hash: str, url: str, is_phishing: bool, confidence: float):
        """
        Store URL analysis result
        
        Args:
            url_hash: SHA-256 hash of normalized URL
            url: Original URL
            is_phishing: Whether URL is phishing
            confidence: Confidence score
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO url_hashes (hash, url, is_phishing, confidence, last_checked)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (url_hash, url, is_phishing, confidence))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store hash: {e}")
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM url_hashes")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM url_hashes WHERE is_phishing = 1")
            phishing = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_urls': total,
                'phishing_urls': phishing,
                'legitimate_urls': total - phishing
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
