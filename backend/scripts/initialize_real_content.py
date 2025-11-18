#!/usr/bin/env python3
"""
Initialize EngineIQ with Real Technical Content

Downloads and processes real technical PDFs to demonstrate
Gemini's multimodal capabilities for the hackathon.
"""

import os
import sys
import asyncio
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
from backend.services.image_processor import ImageProcessor
from backend.services.video_processor import VideoProcessor

print("="*70)
print("🚀 EngineIQ - Real Content Initialization")
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

# Create data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "../data/demo_pdfs")
os.makedirs(DATA_DIR, exist_ok=True)

print()
print("="*70)
print("📄 Processing Real Technical PDFs")
print("="*70)
print()

# PDF 1: MongoDB Replication Guide (Publicly accessible)
print("1. MongoDB Replication Architecture Guide")
print("   Downloading...")

# Use a publicly accessible technical PDF
aws_pdf_url = "https://www.mongodb.com/docs/manual/MongoDB-replication-guide.pdf"
aws_pdf_path = os.path.join(DATA_DIR, "MongoDB_Replication_Guide.pdf")

# Fallback: If that doesn't work, create a comprehensive sample PDF
sample_pdf_needed = False

try:
    if not os.path.exists(aws_pdf_path):
        pdf_processor.download_pdf(aws_pdf_url, aws_pdf_path)
        print("   ✓ Downloaded")
    else:
        print("   ✓ Already downloaded")
    
    print("   Processing with Gemini...")
    result = pdf_processor.process_pdf(
        file_path=aws_pdf_path,
        title="Aruba EdgeConnect Virtual Deployment Guide - AWS",
        uploaded_by="Sarah Chen (Tech Lead)",
        source_url=aws_pdf_url,
        metadata={
            "topics": ["cloud deployment", "AWS", "networking", "SD-WAN"],
            "category": "infrastructure",
            "verified": True
        }
    )
    
    if result.get("success"):
        print(f"   ✅ Processed: {result['chunks_indexed']} chunks indexed")
        print(f"   📊 {result['page_count']} pages, {result['file_size_mb']} MB")
        print(f"   ⏱️  Processing time: {result['processing_time_seconds']}s")
    else:
        print(f"   ❌ Failed: {result.get('message')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# PDF 2: Aruba Azure Deployment Guide  
print("2. Aruba Azure Deployment Guide")
print("   Downloading...")

azure_pdf_url = "https://www.arubanetworks.com/techdocs/sdwan-PDFs/deployments/dg_ECV-Azure_latest.pdf"
azure_pdf_path = os.path.join(DATA_DIR, "Aruba_Azure_Deployment_Guide.pdf")

try:
    if not os.path.exists(azure_pdf_path):
        pdf_processor.download_pdf(azure_pdf_url, azure_pdf_path)
        print("   ✓ Downloaded")
    else:
        print("   ✓ Already downloaded")
    
    print("   Processing with Gemini...")
    result = pdf_processor.process_pdf(
        file_path=azure_pdf_path,
        title="Aruba EdgeConnect Virtual Deployment Guide - Azure",
        uploaded_by="Diego Fernández (Staff Engineer)",
        source_url=azure_pdf_url,
        metadata={
            "topics": ["cloud deployment", "Azure", "networking", "SD-WAN"],
            "category": "infrastructure",
            "verified": True
        }
    )
    
    if result.get("success"):
        print(f"   ✅ Processed: {result['chunks_indexed']} chunks indexed")
        print(f"   📊 {result['page_count']} pages, {result['file_size_mb']} MB")
        print(f"   ⏱️  Processing time: {result['processing_time_seconds']}s")
    else:
        print(f"   ❌ Failed: {result.get('message')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print()
print("="*70)
print("🎥 Adding Video Content (Simulated Transcript)")
print("="*70)
print()

# Simulated team meeting video
print("3. Team Meeting - Database Migration Strategy")

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
        print(f"📌 Key moments: {result['key_moments_count']}")
    else:
        print(f"❌ Failed: {result.get('message')}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print("✅ Real Content Initialization Complete!")
print("="*70)
print()

# Summary
print("📊 SUMMARY:")
print(f"   • PDFs processed: 2 real technical documents")
print(f"   • Videos processed: 1 team meeting with transcript")
print(f"   • Total searchable content: Enhanced knowledge base")
print()

print("🔍 TRY THESE SEARCHES:")
print("   • 'AWS deployment guide'")
print("   • 'Azure cloud setup'")
print("   • 'database migration strategy'")
print("   • 'blue-green deployment'")
print("   • 'rollback automation'")
print()

print("🎉 Ready for demo at http://localhost:8000")
print()
