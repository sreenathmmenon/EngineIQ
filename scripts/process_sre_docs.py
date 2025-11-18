#!/usr/bin/env python3
"""
Process LinkedIn School of SRE documentation
"""

import sys
import os
sys.path.insert(0, '.')

from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService
from qdrant_client.models import PointStruct
import uuid
import time
from pathlib import Path

def process_markdown_file(file_path: Path, gemini: GeminiService, qdrant: QdrantService):
    """Process a single markdown file"""
    
    try:
        # Read content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip if too short
        if len(content) < 200:
            return False
        
        # Extract title from path
        parts = file_path.parts
        if 'courses' in parts:
            idx = parts.index('courses')
            topic_parts = parts[idx+1:-1]
            filename = parts[-1].replace('.md', '').replace('_', ' ').title()
            title = f"SRE: {' - '.join(topic_parts)} - {filename}"
        else:
            title = f"SRE: {file_path.stem}"
        
        # Chunk if too long
        max_chunk_size = 2000
        if len(content) > max_chunk_size:
            # Take first chunk only for speed
            content = content[:max_chunk_size]
        
        # Generate embedding
        embedding = gemini.generate_embedding(content)
        
        # Build correct URL - remove .md and courses/ prefix
        # Example: courses/level101/metrics_and_monitoring/command-line_tools.md
        # -> https://linkedin.github.io/school-of-sre/level101/metrics_and_monitoring/command-line_tools/
        # Find courses in path and build URL from there
        parts_list = list(file_path.parts)
        if 'courses' in parts_list:
            courses_idx = parts_list.index('courses')
            url_parts = parts_list[courses_idx+1:]  # Everything after 'courses'
            url_path = '/'.join(url_parts).replace('.md', '')
            url = f"https://linkedin.github.io/school-of-sre/{url_path}/"
        else:
            url = "https://linkedin.github.io/school-of-sre/"
        
        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "title": title,
                "content": content[:500],  # Preview
                "raw_content": content,
                "source": "GitHub",
                "content_type": "wiki",
                "url": url,
                "indexed_at": int(time.time()),
                "repository": "linkedin/school-of-sre"
            }
        )
        
        # Index to Qdrant
        qdrant.client.upsert(
            collection_name="knowledge_base",
            points=[point],
            wait=True
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {file_path.name}: {e}")
        return False


def main():
    print("="*70)
    print("🔷 LinkedIn School of SRE Processor")
    print("="*70)
    
    # Initialize services
    gemini = GeminiService()
    qdrant = QdrantService()
    
    # Find all markdown files
    base_path = Path("backend/data/school-of-sre")
    md_files = list(base_path.rglob("*.md"))
    
    # Filter to important ones (skip README, CODE_OF_CONDUCT, etc)
    important_files = [
        f for f in md_files 
        if 'courses/level101' in str(f) or 'courses/level102' in str(f)
    ]
    
    print(f"Found {len(md_files)} total files, processing {len(important_files)} course files")
    print()
    
    # Process ALL files
    success_count = 0
    
    for i, file_path in enumerate(important_files, 1):
        print(f"[{i}/{len(important_files)}] Processing {file_path.name}...", end=" ")
        
        if process_markdown_file(file_path, gemini, qdrant):
            success_count += 1
            print("✅")
        else:
            print("⏭️  (skipped)")
    
    print("\n" + "="*70)
    print(f"✅ Successfully indexed {success_count}/{len(important_files)} SRE docs")
    print(f"📚 Topics: Linux, Security, Networking, Python, Databases, Monitoring, etc.")
    print("="*70)


if __name__ == "__main__":
    main()
