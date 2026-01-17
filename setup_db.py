import sqlite3

# Create database
conn = sqlite3.connect('content_feed.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source_type TEXT,
    source_name TEXT,
    description TEXT,
    thumbnail TEXT,
    published_at TEXT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consumed BOOLEAN DEFAULT 0,
    score INTEGER DEFAULT 0,
    estimated_duration INTEGER
)
''')

# Create indexes for better performance
cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumed ON content(consumed)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON content(source_type)')

conn.commit()
conn.close()

print("✅ Database created successfully: content_feed.db")