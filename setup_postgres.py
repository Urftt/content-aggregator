import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="content_db",
    user="content_user",
    password="content_pass"
)

cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS content (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source_type TEXT,
    source_name TEXT,
    description TEXT,
    thumbnail TEXT,
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consumed BOOLEAN DEFAULT FALSE,
    score INTEGER DEFAULT 0,
    estimated_duration INTEGER
)
''')

# Create indexes
cursor.execute('CREATE INDEX IF NOT EXISTS idx_consumed ON content(consumed)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_type ON content(source_type)')
cursor.execute('CREATE INDEX IF NOT EXISTS idx_published_at ON content(published_at DESC)')

conn.commit()
conn.close()

print("✅ PostgreSQL table created successfully!")