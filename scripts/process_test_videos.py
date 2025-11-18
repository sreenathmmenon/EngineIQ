#!/usr/bin/env python3
"""
Process test videos with Gemini transcription
"""

import os
import sys

# Load API key
with open('/Users/sreenath/.env-droid') as f:
    for line in f:
        if line.strip() and not line.startswith('#'):
            key, val = line.strip().split('=', 1)
            os.environ[key] = val

sys.path.insert(0, '/Users/sreenath/Code/Function1-Hackathon-1stPrize/EngineIQ')

from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService
from backend.services.video_processor import VideoProcessor

print("="*70)
print("🎬 PROCESSING TEST VIDEOS WITH GEMINI")
print("="*70)
print()

# Initialize services
print("Initializing services...")
qdrant = QdrantService()
gemini = GeminiService()
video_processor = VideoProcessor(gemini, qdrant)
print("✅ Services initialized")
print()

# Video files
videos = [
    {
        "path": "/Users/sreenath/Code/Function1-Hackathon-1stPrize/EngineIQ/backend/data/test_videos/Performance-debugging-in-DevTools.mp4",
        "title": "Performance Debugging in DevTools"
    },
    {
        "path": "/Users/sreenath/Code/Function1-Hackathon-1stPrize/EngineIQ/backend/data/test_videos/Understanding-MongoDB-Replication-A-Step.mp4",
        "title": "Understanding MongoDB Replication"
    }
]

results = []

for i, video in enumerate(videos, 1):
    print(f"{'='*70}")
    print(f"VIDEO {i}/2: {video['title']}")
    print(f"{'='*70}")
    
    if not os.path.exists(video['path']):
        print(f"❌ File not found: {video['path']}")
        continue
    
    file_size = os.path.getsize(video['path']) / (1024*1024)
    print(f"📄 File: {os.path.basename(video['path'])}")
    print(f"📊 Size: {file_size:.1f} MB")
    print()
    
    try:
        print(f"🔄 Processing with Gemini (this may take 1-2 minutes)...")
        result = video_processor.process_video_file(
            file_path=video['path'],
            title=video['title'],
            uploaded_by="demo_setup"
        )
        
        if result.get('success'):
            print(f"✅ SUCCESS!")
            print(f"   • Chunks indexed: {result['chunks_indexed']}")
            print(f"   • Duration: {result['duration_string']}")
            print(f"   • Transcript length: {result['transcript_length']} chars")
            print(f"   • Processing time: {result['processing_time_seconds']:.1f}s")
            results.append({
                "title": video['title'],
                "success": True,
                "chunks": result['chunks_indexed']
            })
        else:
            print(f"❌ FAILED: {result.get('message')}")
            results.append({
                "title": video['title'],
                "success": False,
                "error": result.get('message')
            })
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        results.append({
            "title": video['title'],
            "success": False,
            "error": str(e)
        })
    
    print()

# Summary
print("="*70)
print("📊 FINAL SUMMARY")
print("="*70)
print()

successes = [r for r in results if r['success']]
failures = [r for r in results if not r['success']]

if successes:
    print(f"✅ SUCCESSES: {len(successes)}")
    for r in successes:
        print(f"   • {r['title']}: {r['chunks']} chunks")
    print()

if failures:
    print(f"❌ FAILURES: {len(failures)}")
    for r in failures:
        print(f"   • {r['title']}: {r.get('error', 'Unknown error')}")
    print()

total_chunks = sum(r.get('chunks', 0) for r in successes)
print(f"📈 Total chunks indexed: {total_chunks}")
print()

if successes:
    print("🎉 VIDEO PROCESSING WORKING!")
    print()
    print("🔍 TRY SEARCHING FOR:")
    print("   • 'performance debugging devtools'")
    print("   • 'mongodb replication'")
    print("   • 'replica sets'")
    print()
    print("🚀 START SERVER:")
    print("   export GEMINI_API_KEY=$(grep GEMINI_API_KEY /Users/sreenath/.env-droid | cut -d= -f2)")
    print("   python3 backend/api/server.py")
    print()
    print("🎨 THEN SEARCH:")
    print("   http://localhost:8000")
else:
    print("⚠️  No videos processed successfully")
    print("   Check errors above")

print("="*70)
