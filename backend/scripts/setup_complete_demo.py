#!/usr/bin/env python3
"""
Complete Demo Setup - Handles failures gracefully
Reports what worked and what failed at the end
"""

import os
import sys
import time
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Check for API key FIRST
if not os.getenv("GEMINI_API_KEY"):
    print("❌ GEMINI_API_KEY not set!")
    print()
    api_key = input("Enter your Gemini API key: ").strip()
    if not api_key:
        print("❌ No API key provided. Exiting.")
        sys.exit(1)
    os.environ["GEMINI_API_KEY"] = api_key
    print("✅ API key set for this session")
    print()

from backend.services.qdrant_service import QdrantService
from backend.services.gemini_service import GeminiService
from backend.services.pdf_processor import PdfProcessor
from backend.services.video_processor import VideoProcessor

# Track results
results = {
    "pdfs_success": [],
    "pdfs_failed": [],
    "videos_success": [],
    "videos_failed": [],
    "total_chunks": 0,
    "total_pages": 0,
    "start_time": time.time()
}

print("="*70)
print("🚀 EngineIQ - Complete Demo Setup")
print("="*70)
print()

# Initialize services
print("Initializing services...")
qdrant = QdrantService()

try:
    gemini = GeminiService()
    test_embedding = gemini.generate_embedding("test")
    print(f"✅ Gemini service initialized (embedding dim: {len(test_embedding)})")
except Exception as e:
    print(f"❌ Gemini service failed: {e}")
    print("Cannot proceed without Gemini API")
    sys.exit(1)

# Initialize processors
pdf_processor = PdfProcessor(gemini, qdrant)
video_processor = VideoProcessor(gemini, qdrant)

print()
print("="*70)
print("📁 STEP 1: Processing Local PDFs")
print("="*70)
print()

# PDF directory
PDF_DIR = os.path.join(os.path.dirname(__file__), "../data/demo_pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# Find all PDFs
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

if pdf_files:
    print(f"Found {len(pdf_files)} PDF(s) in backend/data/demo_pdfs/:")
    for pdf in pdf_files:
        print(f"   • {pdf}")
    print()
    
    # Process each PDF
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"{i}/{len(pdf_files)}: Processing {pdf_file}...")
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        
        try:
            file_size = os.path.getsize(pdf_path) / (1024*1024)
            print(f"   📄 Size: {file_size:.2f} MB")
            
            result = pdf_processor.process_pdf(
                file_path=pdf_path,
                title=pdf_file.replace('.pdf', ''),
                uploaded_by="Admin Demo Setup",
                metadata={
                    "source": "demo_initialization",
                    "category": "technical_documentation",
                    "verified": True,
                    "added_at": datetime.now().isoformat()
                }
            )
            
            if result.get("success"):
                print(f"   ✅ SUCCESS")
                print(f"      • Chunks: {result['chunks_indexed']}")
                print(f"      • Pages: {result['page_count']}")
                print(f"      • Time: {result['processing_time_seconds']:.1f}s")
                
                results["pdfs_success"].append({
                    "name": pdf_file,
                    "chunks": result['chunks_indexed'],
                    "pages": result['page_count'],
                    "time": result['processing_time_seconds']
                })
                results["total_chunks"] += result['chunks_indexed']
                results["total_pages"] += result['page_count']
            else:
                print(f"   ❌ FAILED: {result.get('message', 'Unknown error')}")
                results["pdfs_failed"].append({
                    "name": pdf_file,
                    "error": result.get('message', 'Unknown error')
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)[:100]}")
            results["pdfs_failed"].append({
                "name": pdf_file,
                "error": str(e)[:100]
            })
        
        print()
else:
    print("⚠️  No PDFs found in backend/data/demo_pdfs/")
    print()
    print("💡 To add PDFs:")
    print("   1. Download any technical PDF documents")
    print("   2. Put them in: backend/data/demo_pdfs/")
    print("   3. Run this script again")
    print()

print("="*70)
print("🎥 STEP 2: Adding Simulated Video Content")
print("="*70)
print()

# Video 1: Team Meeting
print("1. Team Meeting - Database Migration Strategy")

team_meeting_transcript = """
Discussion about database migration strategy for Q4. 

Sarah Chen (Tech Lead) at 23:15: "I recommend we implement a blue-green deployment approach for the database migration. This will allow us to switch between old and new database versions with minimal downtime."

Diego Fernández (Staff Engineer) at 31:40: "I have concerns about the downtime during the switch. Even a few seconds of downtime could affect critical transactions. We should implement rollback automation first before proceeding."

Maria Gonzalez (Engineer) at 35:20: "What about the authentication service? It's tightly coupled with the database schema."

Sarah Chen at 36:45: "Good point Maria. We'll need to version the API to support both old and new schemas during the migration period."

Priya Sharma (Junior Engineer) at 38:20: "Can you explain the testing procedures? I want to make sure I understand how to validate the migration works correctly."

Sarah Chen at 39:30: "Absolutely Priya. We'll have three testing phases: staging validation, canary deployment with 5% traffic, then full rollout. I'll document the test cases this week."

Diego Fernández at 42:15: "I'll write the rollback automation scripts and get them reviewed by Friday."

Action items:
- Sarah: Document migration test cases (by Wednesday)
- Diego: Implement rollback automation (by Friday)  
- Maria: Update authentication service API versioning (by Thursday)
- Priya: Learn and validate staging migration process (by Monday)
"""

try:
    result = video_processor.process_video_metadata(
        title="Team Meeting - Database Migration Strategy Q4",
        transcript=team_meeting_transcript,
        duration="45 minutes",
        speakers=["Sarah Chen", "Diego Fernández", "Maria Gonzalez", "Priya Sharma"],
        key_moments=[
            {"timestamp": "23:15", "content": "Sarah explains blue-green deployment approach"},
            {"timestamp": "31:40", "content": "Diego raises downtime concerns"},
            {"timestamp": "35:20", "content": "Maria asks about authentication service"},
            {"timestamp": "38:20", "content": "Priya asks about testing procedures"},
            {"timestamp": "42:15", "content": "Diego commits to rollback automation"}
        ],
        uploaded_by="Sarah Chen (Tech Lead)",
        metadata={
            "meeting_type": "technical_planning",
            "quarter": "Q4",
            "topics": ["database migration", "blue-green deployment", "rollback automation"],
            "category": "meeting",
            "added_at": datetime.now().isoformat()
        }
    )
    
    if result.get("success") and result.get("chunks_indexed", 0) > 0:
        print(f"✅ SUCCESS")
        print(f"   • Chunks: {result['chunks_indexed']}")
        print(f"   • Speakers: {', '.join(result['speakers'])}")
        print(f"   • Duration: {result['duration']}")
        
        results["videos_success"].append({
            "name": "Team Meeting - Database Migration Strategy Q4",
            "chunks": result['chunks_indexed'],
            "speakers": len(result['speakers'])
        })
        results["total_chunks"] += result['chunks_indexed']
    else:
        print(f"⚠️  PARTIAL: Processed but no chunks indexed")
        results["videos_failed"].append({
            "name": "Team Meeting - Database Migration Strategy Q4",
            "error": "No chunks indexed"
        })
        
except Exception as e:
    print(f"❌ ERROR: {str(e)[:100]}")
    results["videos_failed"].append({
        "name": "Team Meeting - Database Migration Strategy Q4",
        "error": str(e)[:100]
    })

print()

# Video 2: Architecture Discussion
print("2. Architecture Review - Microservices Discussion")

arch_transcript = """
Architecture review meeting discussing microservices migration.

Diego Fernández at 10:00: "We need to break down the monolith into microservices. I suggest starting with the authentication service as it's the most decoupled."

Sarah Chen at 12:30: "Agreed. We should also implement service mesh for observability. Istio would give us traffic management, security, and monitoring out of the box."

Priya Sharma at 15:45: "What about the database? Should each microservice have its own database?"

Diego at 16:20: "Yes, that's the database-per-service pattern. It provides better isolation and scalability. However, we need to handle distributed transactions carefully."

Maria Gonzalez at 18:00: "For inter-service communication, should we use REST or gRPC?"

Sarah at 19:15: "I recommend gRPC for internal services due to better performance, and REST for external APIs. We can use API Gateway to handle protocol translation."

Key decisions:
- Start with authentication service migration
- Implement Istio service mesh
- Database-per-service pattern
- gRPC for internal, REST for external APIs
"""

try:
    result = video_processor.process_video_metadata(
        title="Architecture Review - Microservices Migration Strategy",
        transcript=arch_transcript,
        duration="30 minutes",
        speakers=["Diego Fernández", "Sarah Chen", "Priya Sharma", "Maria Gonzalez"],
        key_moments=[
            {"timestamp": "10:00", "content": "Diego proposes breaking down monolith"},
            {"timestamp": "12:30", "content": "Sarah suggests service mesh"},
            {"timestamp": "15:45", "content": "Priya asks about database strategy"},
            {"timestamp": "18:00", "content": "Maria asks about communication protocols"}
        ],
        uploaded_by="Diego Fernández",
        metadata={
            "meeting_type": "architecture_review",
            "topics": ["microservices", "service mesh", "API design"],
            "category": "meeting",
            "added_at": datetime.now().isoformat()
        }
    )
    
    if result.get("success") and result.get("chunks_indexed", 0) > 0:
        print(f"✅ SUCCESS")
        print(f"   • Chunks: {result['chunks_indexed']}")
        print(f"   • Speakers: {', '.join(result['speakers'])}")
        
        results["videos_success"].append({
            "name": "Architecture Review - Microservices Migration",
            "chunks": result['chunks_indexed'],
            "speakers": len(result['speakers'])
        })
        results["total_chunks"] += result['chunks_indexed']
    else:
        print(f"⚠️  PARTIAL: Processed but no chunks indexed")
        results["videos_failed"].append({
            "name": "Architecture Review - Microservices Migration",
            "error": "No chunks indexed"
        })
        
except Exception as e:
    print(f"❌ ERROR: {str(e)[:100]}")
    results["videos_failed"].append({
        "name": "Architecture Review - Microservices Migration",
        "error": str(e)[:100]
    })

print()

# Calculate totals
elapsed_time = time.time() - results["start_time"]
total_success = len(results["pdfs_success"]) + len(results["videos_success"])
total_failed = len(results["pdfs_failed"]) + len(results["videos_failed"])

print()
print("="*70)
print("📊 FINAL REPORT")
print("="*70)
print()

# Success Summary
print("✅ SUCCESSES:")
print(f"   PDFs: {len(results['pdfs_success'])}")
for pdf in results["pdfs_success"]:
    print(f"      • {pdf['name']}: {pdf['chunks']} chunks, {pdf['pages']} pages")

print(f"   Videos: {len(results['videos_success'])}")
for video in results["videos_success"]:
    print(f"      • {video['name']}: {video['chunks']} chunks")

print()

# Failure Summary
if results["pdfs_failed"] or results["videos_failed"]:
    print("❌ FAILURES:")
    if results["pdfs_failed"]:
        print(f"   PDFs: {len(results['pdfs_failed'])}")
        for pdf in results["pdfs_failed"]:
            print(f"      • {pdf['name']}")
            print(f"        Error: {pdf['error']}")
    
    if results["videos_failed"]:
        print(f"   Videos: {len(results['videos_failed'])}")
        for video in results["videos_failed"]:
            print(f"      • {video['name']}")
            print(f"        Error: {video['error']}")
    print()

# Statistics
print("📈 STATISTICS:")
print(f"   Total items processed: {total_success}")
print(f"   Total items failed: {total_failed}")
print(f"   Total chunks indexed: {results['total_chunks']}")
if results["total_pages"] > 0:
    print(f"   Total pages processed: {results['total_pages']}")
print(f"   Processing time: {elapsed_time:.1f} seconds")
print()

# Next steps
if total_success > 0:
    print("🎉 SUCCESS! Your content is ready!")
    print()
    print("🔍 TRY SEARCHING FOR:")
    if results["pdfs_success"]:
        print("   • Content from your PDFs")
    if results["videos_success"]:
        print("   • 'database migration strategy'")
        print("   • 'blue-green deployment'")
        print("   • 'microservices architecture'")
    print()
    print("🚀 START SERVER:")
    print("   export GEMINI_API_KEY=your_key")
    print("   python3 backend/api/server.py")
    print()
    print("🎨 THEN VISIT:")
    print("   Main UI:   http://localhost:8000")
    print("   Admin UI:  http://localhost:8000/admin.html")
else:
    print("⚠️  NO CONTENT PROCESSED")
    print()
    print("To add content:")
    print("   1. Put PDF files in: backend/data/demo_pdfs/")
    print("   2. Run this script again")

print()
print("="*70)
