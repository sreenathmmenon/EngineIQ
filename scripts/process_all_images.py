#!/usr/bin/env python3
"""
Process multiple architecture diagram images
"""

import sys
sys.path.insert(0, '.')

from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService
from qdrant_client.models import PointStruct
import uuid
import time

def process_single_image(image_path: str, title: str, gemini: GeminiService, qdrant: QdrantService):
    """Process a single image"""
    
    print(f"\n📸 Processing: {image_path}")
    
    try:
        # Upload and analyze image with Gemini
        print("⏳ Uploading to Gemini File API...", end=" ")
        file_ref = gemini.upload_file(image_path)
        print("✅")
        
        # Generate description
        print("🤖 Analyzing image content...", end=" ")
        prompt = """Analyze this architecture diagram in detail. Describe:
1. What type of system/architecture is shown (e.g., streaming, e-commerce, etc.)
2. Key components and their roles
3. How components connect and communicate
4. Scalability and performance features
5. Technology stack visible in the diagram
6. Data flow and processing pipelines
7. CDN, caching, and optimization strategies

Be comprehensive and technical."""
        
        description = gemini.generate_content_with_file(file_ref, prompt)
        print("✅")
        
        print(f"📝 Generated {len(description)} chars of description")
        print(f"Preview: {description[:150]}...")
        
        # Generate embedding from description
        print("🔢 Generating embedding...", end=" ")
        embedding = gemini.generate_embedding(description)
        print("✅")
        
        # Extract filename
        filename = image_path.split('/')[-1]
        
        # Create point
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "title": title,
                "content": description[:500],  # Preview
                "raw_content": description,
                "source": "Images",
                "content_type": "image",
                "file_path": image_path,
                "file_name": filename,
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*70)
    print("🖼️  Processing Architecture Diagrams")
    print("="*70)
    
    # Initialize services
    gemini = GeminiService()
    qdrant = QdrantService()
    
    # Define images to process
    images = [
        {
            "path": "/Users/sreenath/Downloads/ByteByteGo_Hotstar-Architecture-diagram.png",
            "title": "Hotstar Architecture - Video Streaming Platform at Scale"
        }
    ]
    
    success_count = 0
    
    for img in images:
        if process_single_image(img["path"], img["title"], gemini, qdrant):
            success_count += 1
    
    print("\n" + "="*70)
    print(f"✅ Successfully indexed {success_count}/{len(images)} diagram(s)!")
    print("\n🔍 Search queries to try:")
    print("   - 'video streaming architecture'")
    print("   - 'cdn content delivery'")
    print("   - 'hotstar scalability'")
    print("="*70)

if __name__ == "__main__":
    main()
