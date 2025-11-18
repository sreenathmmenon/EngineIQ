#!/usr/bin/env python3
"""
Process architecture diagram image
"""

import sys
sys.path.insert(0, '.')

from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService
from qdrant_client.models import PointStruct
import uuid
import time

def process_image():
    print("="*70)
    print("🖼️  Processing HA Architecture Diagram")
    print("="*70)
    
    # Initialize services
    gemini = GeminiService()
    qdrant = QdrantService()
    
    image_path = "/Users/sreenath/Downloads/Unicon_HA_Architecture-diagram.png"
    
    print(f"\n📸 Processing: {image_path}")
    
    # Upload and analyze image with Gemini
    print("⏳ Uploading to Gemini File API...", end=" ")
    file_ref = gemini.upload_file(image_path)
    print("✅")
    
    # Generate description
    print("🤖 Analyzing image content...", end=" ")
    prompt = """Analyze this architecture diagram in detail. Describe:
1. What type of system/architecture is shown
2. Key components and their roles
3. How components connect and communicate
4. High availability and redundancy features
5. Technology stack visible in the diagram
6. Security considerations
7. Data flow patterns

Be comprehensive and technical."""
    
    description = gemini.generate_content_with_file(file_ref, prompt)
    print("✅")
    
    print(f"\n📝 Generated {len(description)} chars of description")
    print(f"Preview: {description[:200]}...\n")
    
    # Generate embedding from description
    print("🔢 Generating embedding...", end=" ")
    embedding = gemini.generate_embedding(description)
    print("✅")
    
    # Create point
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "title": "HA Architecture Diagram - High Availability System Design",
            "content": description[:500],  # Preview
            "raw_content": description,
            "source": "Images",
            "content_type": "image",
            "file_path": image_path,
            "file_name": "Unicon_HA_Architecture-diagram.png",
            "indexed_at": int(time.time())
        }
    )
    
    # Index to Qdrant
    print("💾 Indexing to Qdrant...", end=" ")
    qdrant.client.upsert(
        collection_name="knowledge_base",
        points=[point],
        wait=True
    )
    print("✅")
    
    print("\n" + "="*70)
    print("✅ Successfully indexed architecture diagram!")
    print("🔍 Search queries to try:")
    print("   - 'high availability architecture'")
    print("   - 'system redundancy design'")
    print("   - 'load balancer configuration'")
    print("="*70)

if __name__ == "__main__":
    process_image()
