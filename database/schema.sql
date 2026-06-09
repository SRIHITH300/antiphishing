-- Database schema for phishing detection system
-- SQLite database for hash-based URL lookup

-- URL hashes table (main lookup table)
CREATE TABLE IF NOT EXISTS url_hashes (
    hash TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    is_phishing BOOLEAN NOT NULL,
    confidence REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_count INTEGER DEFAULT 1
);

-- Index for fast hash lookups
CREATE INDEX IF NOT EXISTS idx_hash ON url_hashes(hash);

-- Index for filtering by classification
CREATE INDEX IF NOT EXISTS idx_is_phishing ON url_hashes(is_phishing);

-- Index for filtering by confidence
CREATE INDEX IF NOT EXISTS idx_confidence ON url_hashes(confidence);

-- Optional: User accounts table (if authentication is enabled)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Optional: User history table (if tracking is enabled)
CREATE TABLE IF NOT EXISTS user_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    url_hash TEXT NOT NULL,
    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (url_hash) REFERENCES url_hashes(hash)
);

-- Optional: Feedback table (for model improvement)
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT NOT NULL,
    user_reported_phishing BOOLEAN NOT NULL,
    model_predicted_phishing BOOLEAN NOT NULL,
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_hash) REFERENCES url_hashes(hash)
);
