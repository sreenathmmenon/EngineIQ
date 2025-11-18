#!/usr/bin/env python3
"""
Process PDFs from local folder
Put your PDFs in backend/data/demo_pdfs/ and run this script
"""

import os
import sys
import time

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

print("="*70)
print("🚀 EngineIQ - Process Local PDFs")
print("="*70)
print()

# Initialize services
print("Initializing services...")
qdrant = QdrantService()

try:
    gemini = GeminiService()
    # Test it works
    test_embedding = gemini.generate_embedding("test")
    print(f"✅ Gemini service initialized (embedding dim: {len(test_embedding)})")
except Exception as e:
    print(f"❌ Gemini service failed: {e}")
    print("Please check your GEMINI_API_KEY")
    sys.exit(1)

# Initialize processors
pdf_processor = PdfProcessor(gemini, qdrant)
video_processor = VideoProcessor(gemini, qdrant)

# PDF directory
PDF_DIR = os.path.join(os.path.dirname(__file__), "../data/demo_pdfs")

print()
print("="*70)
print("📁 Looking for PDFs in: backend/data/demo_pdfs/")
print("="*70)
print()

# Find all PDFs
pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith('.pdf')]

if not pdf_files:
    print("❌ No PDF files found!")
    print()
    print("📋 Instructions:")
    print("   1. Download any technical PDF documents")
    print("   2. Put them in: backend/data/demo_pdfs/")
    print("   3. Run this script again")
    print()
    print("💡 Suggested PDFs to download:")
    print("   • Kubernetes documentation")
    print("   • AWS architecture guides")
    print("   • Database migration guides")
    print("   • Any technical whitepapers")
    print()
    
    # Add simulated video anyway
    print("="*70)
    print("🎥 Adding Simulated Video Content")
    print("="*70)
    print()
    
    print("Adding: Team Meeting - Database Migration Strategy")
    
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
                "category": "meeting"
            }
        )
        
        if result.get("success"):
            print(f"✅ Video processed: {result['chunks_indexed']} chunks indexed")
            print(f"👥 Speakers: {', '.join(result['speakers'])}")
            print(f"⏱️  Duration: {result['duration']}")
        else:
            print(f"❌ Failed: {result.get('message')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    sys.exit(0)

print(f"Found {len(pdf_files)} PDF(s):")
for pdf in pdf_files:
    print(f"   • {pdf}")
print()

# Process each PDF
processed_count = 0
failed_count = 0

for i, pdf_file in enumerate(pdf_files, 1):
    print("="*70)
    print(f"{i}. Processing: {pdf_file}")
    print("="*70)
    
    pdf_path = os.path.join(PDF_DIR, pdf_file)
    
    try:
        print(f"   📄 File size: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")
        print(f"   🔄 Uploading to Gemini and processing...")
        
        result = pdf_processor.process_pdf(
            file_path=pdf_path,
            title=pdf_file.replace('.pdf', ''),
            uploaded_by="Admin",
            metadata={
                "source": "local_upload",
                "category": "technical_documentation",
                "verified": True
            }
        )
        
        if result.get("success"):
            print(f"   ✅ Success!")
            print(f"      • Chunks indexed: {result['chunks_indexed']}")
            print(f"      • Pages: {result['page_count']}")
            print(f"      • Processing time: {result['processing_time_seconds']}s")
            processed_count += 1
        else:
            print(f"   ❌ Failed: {result.get('message')}")
            failed_count += 1
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed_count += 1
    
    print()

# Add simulated video
print("="*70)
print("🎥 Adding Simulated Video Content")
print("="*70)
print()

print("Adding: Team Meeting - Database Migration Strategy")

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
            "category": "meeting"
        }
    )
    
    if result.get("success"):
        print(f"✅ Video processed: {result['chunks_indexed']} chunks indexed")
        print(f"👥 Speakers: {', '.join(result['speakers'])}")
        print(f"⏱️  Duration: {result['duration']}")
    else:
        print(f"❌ Failed: {result.get('message')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print("✅ Processing Complete!")
print("="*70)
print()

print("📊 SUMMARY:")
print(f"   • PDFs processed successfully: {processed_count}")
if failed_count > 0:
    print(f"   • PDFs failed: {failed_count}")
print(f"   • Videos added: 1")
print()

if processed_count > 0:
    print("🔍 NOW TRY SEARCHING FOR:")
    print("   • Content from your PDFs")
    print("   • 'database migration strategy'")
    print("   • 'blue-green deployment'")
    print("   • 'rollback automation'")
    print()

print("🎉 Ready for demo at http://localhost:8000")
print()
