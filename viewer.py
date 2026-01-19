"""
Content Aggregator Viewer
A simple Streamlit app to browse collected content and mark items as consumed.
"""

import os
import streamlit as st
import psycopg2
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def fetch_content(consumed_filter="all"):
    """Fetch content from database with optional consumed filter."""
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT id, title, url, source_type, source_name, 
               description, thumbnail, published_at, collected_at, 
               consumed, estimated_duration
        FROM content
    """
    
    if consumed_filter == "unconsumed":
        query += " WHERE consumed = FALSE"
    elif consumed_filter == "consumed":
        query += " WHERE consumed = TRUE"
    
    query += " ORDER BY published_at DESC"
    
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    conn.close()
    
    return pd.DataFrame(rows, columns=columns)


def mark_as_consumed(content_id, consumed=True):
    """Mark content item as consumed or unconsumed."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE content SET consumed = %s WHERE id = %s",
        (consumed, content_id)
    )
    
    conn.commit()
    conn.close()


# Streamlit app configuration
st.set_page_config(
    page_title="Content Aggregator",
    page_icon="📚",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .content-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .thumbnail {
        border-radius: 8px;
        width: 100%;
        max-width: 320px;
    }
    .metadata {
        color: #666;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Content Aggregator")
st.markdown("Your curated content, distraction-free.")

# Sidebar filters
st.sidebar.header("Filters")
consumed_filter = st.sidebar.radio(
    "Show:",
    ["all", "unconsumed", "consumed"],
    index=1  # Default to unconsumed
)

# Fetch and display content
df = fetch_content(consumed_filter)

if df.empty:
    st.info("No content found. Check your n8n workflows are running!")
else:
    st.write(f"**{len(df)} items**")
    
    # Display each item
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col1:
            # Thumbnail
            if row['thumbnail']:
                st.image(row['thumbnail'], use_container_width=True)
            else:
                st.write("🎥")
        
        with col2:
            # Title with link
            st.markdown(f"### [{row['title']}]({row['url']})")
            
            # Metadata line
            duration_text = f"{row['estimated_duration']} min" if row['estimated_duration'] else "Duration unknown"
            published_date = row['published_at'].strftime('%Y-%m-%d %H:%M') if row['published_at'] else "Unknown date"
            
            st.markdown(
                f"<p class='metadata'>📺 {row['source_name']} | "
                f"📅 {published_date} | "
                f"⏱️ {duration_text}</p>",
                unsafe_allow_html=True
            )
            
            # Description
            if row['description']:
                description = row['description']
                if len(description) > 300:
                    description = description[:300] + "..."
                st.write(description)
        
        with col3:
            # Consumed toggle button
            st.write("")  # Spacing
            st.write("")  # Spacing
            if row['consumed']:
                if st.button("✅ Watched", key=f"consumed_{row['id']}", use_container_width=True):
                    mark_as_consumed(row['id'], False)
                    st.rerun()
            else:
                if st.button("Mark as Watched", key=f"unconsumed_{row['id']}", use_container_width=True):
                    mark_as_consumed(row['id'], True)
                    st.rerun()
        
        st.divider()

# Stats in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Stats")
total_df = fetch_content("all")
if not total_df.empty:
    total_count = len(total_df)
    consumed_count = total_df['consumed'].sum()
    unconsumed_count = total_count - consumed_count
    
    st.sidebar.metric("Total Items", total_count)
    st.sidebar.metric("Watched", consumed_count)
    st.sidebar.metric("To Watch", unconsumed_count)
    
    # Calculate total watch time
    total_duration = total_df[total_df['estimated_duration'].notna()]['estimated_duration'].sum()
    if total_duration > 0:
        hours = int(total_duration // 60)
        minutes = int(total_duration % 60)
        st.sidebar.metric("Total Content", f"{hours}h {minutes}m")