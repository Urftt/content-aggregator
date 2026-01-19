# Content Aggregator

Personal content aggregator to combat doomscrolling. Automatically collects videos, articles, and podcasts from your preferred sources without algorithmic distractions.

## Overview

Instead of opening YouTube/RSS apps and getting sucked into endless recommendations, this system:

- Collects content from sources you actually want
- Filters out junk (shorts, clickbait)
- Presents everything in a clean interface
- No algorithms, no distractions, just your content

## Current Status

- ✅ PostgreSQL database with content schema
- ✅ Docker Compose setup (PostgreSQL + n8n)
- ✅ YouTube collection via n8n workflows
- 🚧 Transitioning to pure Python collectors
- ⏳ Content viewer (not yet built)
- ⏳ RSS/podcast collection (planned)

## Tech Stack

- **Python 3.13+** - scripting and automation
- **PostgreSQL** - content storage
- **Docker Compose** - container orchestration
- **n8n** - current automation workflows (being phased out)
- **uv** - Python package management
- **Streamlit** - planned for content viewer

## Prerequisites

- Docker Desktop installed
- Python 3.13+
- uv package manager

## Quick Start

### 1. Start PostgreSQL

```bash
docker-compose up -d postgres
```

### 2. Create database schema

```bash
uv run python setup_postgres.py
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your YouTube API key
```

### 4. (Optional) Start n8n for YouTube collection

```bash
docker-compose up -d
```

## Architecture

### Database Schema

**Table: content**

```sql
id                SERIAL PRIMARY KEY
title             TEXT NOT NULL
url               TEXT UNIQUE NOT NULL
source_type       TEXT                    -- 'youtube', 'rss', 'podcast'
source_name       TEXT
description       TEXT
thumbnail         TEXT
published_at      TIMESTAMP
collected_at      TIMESTAMP DEFAULT NOW()
consumed          BOOLEAN DEFAULT FALSE
score             INTEGER DEFAULT 0       -- For future content ranking
estimated_duration INTEGER                 -- In seconds
```

### Project Structure

```
content-aggregator/
├── collectors/              # Content collection scripts (planned)
│   ├── youtube.py          # YouTube video collector (not yet built)
│   ├── rss.py              # RSS feed collector (planned)
│   └── podcast.py          # Podcast collector (planned)
├── viewer/                 # Content viewing interface (planned)
│   └── app.py              # Streamlit dashboard
├── setup_postgres.py       # Database initialization
├── docker-compose.yml      # Container definitions (PostgreSQL + n8n)
├── .env.example            # Environment template
├── pyproject.toml          # Python dependencies
└── README.md
```

## Transition from n8n to Pure Python

### Why the change

- n8n workflows become click-heavy with multiple sources
- Pure Python gives more flexibility and version control
- Easier to customize filtering/scoring logic
- Better for ML integration later

### Migration plan

1. Build YouTube collector script (`collectors/youtube.py`)
2. Add cron/scheduler for automation
3. Deprecate n8n workflows
4. Keep PostgreSQL in Docker for simplicity

## YouTube API Setup

### Get API credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable YouTube Data API v3
4. Create API credentials (API key)
5. Add key to `.env` file

### API Rate Limits

- 10,000 units/day (free tier)
- Each search query costs ~100 units
- Plenty for personal use (~100 queries/day)

## Environment Variables

Create a `.env` file:

```bash
# YouTube API
YOUTUBE_API_KEY=your_api_key_here

# Database (matches docker-compose.yml)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_db
DB_USER=content_user
DB_PASSWORD=content_pass
```

## Development

### Database Connection

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="content_db",
    user="content_user",
    password="content_pass"
)
```

### Add Python Dependencies

```bash
uv add package-name
```

### Docker Commands

```bash
# Start all services (PostgreSQL + n8n)
docker-compose up -d

# Start only PostgreSQL
docker-compose up -d postgres

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Database Management

```bash
# Connect to PostgreSQL
docker exec -it content-aggregator-db psql -U content_user -d content_db
```

**Useful queries:**

```sql
-- Count total content items
SELECT COUNT(*) FROM content;

-- View unconsumed content
SELECT * FROM content
WHERE consumed = false
ORDER BY published_at DESC
LIMIT 10;

-- Delete specific item
DELETE FROM content WHERE url = 'specific_url';

-- Mark content as consumed
UPDATE content SET consumed = true WHERE id = 1;
```

## YouTube Channels Being Collected

Currently configured channels:
- Stuff Made Here (UCj1VqrHhDte54oLgPG4xpuQ)

(Add more channels through n8n workflows or future Python collector)

## Next Steps

### Immediate priorities

- [ ] Build `collectors/youtube.py` - Python script to replace n8n YouTube workflow
- [ ] Add scheduling (cron or APScheduler)
- [ ] Build Streamlit viewer app
- [ ] Implement filtering/scoring logic (criteria TBD)

### Future enhancements

- [ ] RSS feed collection
- [ ] Podcast collection
- [ ] ML-based content scoring
- [ ] Daily digest emails
- [ ] Mobile-friendly interface

## Design Philosophy

- **Keep it simple** - resist over-engineering
- **Focus on solving the doomscroll problem** - quality over quantity
- **Prioritize filtering quality** - better to miss content than get overwhelmed
- **No algorithm manipulation** - you choose sources, not an AI

## Technical Notes

**Why PostgreSQL over SQLite?**
Better for concurrent access, native n8n support, good for future expansion.

**Why uv?**
Faster than pip, better dependency management, modern Python tooling.

**Code style:**
PEP8 compliant, type hints encouraged.

## License

MIT

## Contributing

This is a personal project, but if you're building something similar, feel free to fork and adapt to your needs.
