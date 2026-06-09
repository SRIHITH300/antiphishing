-- Seed data for known legitimate and phishing URLs
-- These provide instant results without ML inference

-- Known legitimate URLs (popular websites)
INSERT OR IGNORE INTO url_hashes (hash, url, is_phishing, confidence) VALUES
('a3c3e6e9f8b6d4c2a1e5f8d9c7b5a4e3', 'https://www.google.com', 0, 0.99),
('b4d5f7a8c9e1b2d3e4f5a6b7c8d9e1f2', 'https://www.facebook.com', 0, 0.99),
('c5e6a7b8d9f1c2e3d4f5a6b7c8d9e1f2', 'https://www.amazon.com', 0, 0.99),

('d6f7b8c9e1a2d3f4e5a6b7c8d9e1f2a3', 'https://www.youtube.com', 0, 0.99),
('e7a8c9d1f2b3e4a5d6f7b8c9e1a2d3f4', 'https://www.twitter.com', 0, 0.99),
('f8b9d1e2a3c4f5b6e7d8a9c1e2f3b4d5', 'https://www.linkedin.com', 0, 0.99),
('a9c1e2f3d4b5a6c7e8f9d1a2b3c4e5f6', 'https://www.github.com', 0, 0.99),
('b1d2f3e4a5c6b7d8e9f1a2c3d4e5f6a7', 'https://www.stackoverflow.com', 0, 0.99),
('c2e3a4f5b6d7c8e9a1f2b3d4e5a6c7f8', 'https://www.reddit.com', 0, 0.99),
('d3f4b5a6c7e8d9f1a2b3c4e5f6d7a8b9', 'https://www.wikipedia.org', 0, 0.99),
('e4a5c6b7d8f9e1a2c3d4f5b6a7c8e9d1', 'https://www.microsoft.com', 0, 0.99),
('f5b6d7c8e9a1f2b3d4e5a6c7b8d9e1f2', 'https://www.apple.com', 0, 0.99),
('a6c7e8d9f1a2b3c4e5f6d7a8b9c1e2f3', 'https://www.netflix.com', 0, 0.99),
('b7d8f9e1a2c3d4f5b6a7c8e9d1f2a3b4', 'https://www.instagram.com', 0, 0.99);

-- Example phishing URLs (synthetic/training examples)
-- Note: In production, these would come from known phishing databases
-- Format: hash, url, is_phishing (1=phishing), confidence
INSERT OR IGNORE INTO url_hashes (hash, url, is_phishing, confidence) VALUES
('1a2b3c4d5e6f7a8b9c1d2e3f4a5b6c7d', 'http://g00gle-verify.com/login', 1, 0.95),
('2b3c4d5e6f7a8b9c1d2e3f4a5b6c7d8e', 'http://paypal-security.tk/update', 1, 0.98),
('3c4d5e6f7a8b9c1d2e3f4a5b6c7d8e9f', 'http://amazon-account-verify.ml/signin', 1, 0.97),
('4d5e6f7a8b9c1d2e3f4a5b6c7d8e9f1a', 'http://192.168.1.1/facebook/login', 1, 0.96),
('5e6f7a8b9c1d2e3f4a5b6c7d8e9f1a2b', 'http://secure-banking-update.ga/verify', 1, 0.94);

-- Note: In production, integrate with:
-- - PhishTank API
-- - Google Safe Browsing API
-- - OpenPhish feeds
-- - URLhaus database
