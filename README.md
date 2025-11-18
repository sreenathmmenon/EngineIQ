# EngineIQ

**AI-Powered Enterprise Knowledge Search with Multimodal Intelligence**

EngineIQ is an intelligent enterprise search system that indexes and searches across multiple data sources using advanced AI. It leverages Google's Gemini API for multimodal content processing and Qdrant for vector search, providing instant access to organizational knowledge.

---

## Features

### Multimodal Content Processing
- **Documents**: PDF processing with text extraction and analysis
- **Code**: GitHub repository indexing with semantic understanding
- **Conversations**: Slack channel integration with context preservation
- **Videos**: Automatic transcription and content extraction
- **Images**: Architecture diagram analysis with vision AI
- **Wiki**: Markdown documentation processing

### Intelligent Search
- **Semantic Search**: Vector-based similarity matching using 768-dimensional embeddings
- **Agentic Workflow**: 8-node LangGraph agent system for intelligent query processing
- **Permission-Aware**: Role-based access control and sensitivity filtering
- **Real-time Indexing**: Continuous pipeline from upload to searchable content

### Enterprise Ready
- Clean, professional UI with light/dark themes
- Admin dashboard for content management
- RESTful API for integration
- Scalable vector database architecture

---

## Architecture

```
┌─────────────────┐
│  Data Sources   │
│  Box, Slack,    │
│  GitHub, Wiki,  │
│  Videos, Images │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini API     │
│  - Embeddings   │
│  - Vision       │
│  - Analysis     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Qdrant VectorDB│
│  - Indexing     │
│  - Search       │
│  - Filtering    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangGraph Agent│
│  - Query Parse  │
│  - Filter       │
│  - Rerank       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │
│  - Search API   │
│  - Admin API    │
│  - Web UI       │
└─────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.9+
- Qdrant running on localhost:6333
- Google Gemini API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd EngineIQ
```

2. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Set up environment**
```bash
export GEMINI_API_KEY="your-api-key-here"
export GOOGLE_API_KEY="your-api-key-here"  # Same as GEMINI_API_KEY
```

4. **Start Qdrant** (if not running)
```bash
docker run -p 6333:6333 qdrant/qdrant
```

5. **Run the server**
```bash
python -m backend.api.server
```

6. **Access the application**
- Search UI: http://localhost:8000/
- Admin Dashboard: http://localhost:8000/admin.html

---

## Usage

### Search Interface
1. Open http://localhost:8000/
2. Enter your search query (e.g., "high availability architecture")
3. View results with source attribution and relevance ranking
4. Expand results to see full content
5. Click source links to access original documents

### Admin Dashboard
1. Open http://localhost:8000/admin.html
2. View system statistics and data source counts
3. Drag and drop files to upload (PDF, images, videos, documents)
4. Monitor processing status
5. Newly uploaded content is immediately searchable

### Processing Content

**Process PDFs:**
```python
from backend.services.pdf_processor import PDFProcessor
from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService

gemini = GeminiService()
qdrant = QdrantService()
pdf_processor = PDFProcessor(gemini, qdrant)

pdf_processor.process_pdf("document.pdf", title="My Document")
```

**Process Images:**
```python
from backend.services.image_processor import ImageProcessor

image_processor = ImageProcessor(gemini, qdrant)
image_processor.process_image("diagram.png", title="Architecture Diagram")
```

**Process Videos:**
```python
from backend.services.video_processor import VideoProcessor

video_processor = VideoProcessor(gemini, qdrant)
video_processor.process_video_file("tutorial.mp4", title="Tutorial Video")
```

---

## API Reference

### Search API

**POST /api/search**

Search for content across all indexed sources.

Request:
```json
{
  "query": "kubernetes networking",
  "limit": 10,
  "user_id": "user123"
}
```

Response:
```json
{
  "results": [
    {
      "id": "doc-123",
      "title": "Kubernetes Networking Guide",
      "content": "...",
      "score": 0.87,
      "source": "GitHub",
      "url": "https://github.com/...",
      "metadata": {...}
    }
  ],
  "agent_insights": {
    "documents_searched": 100,
    "documents_filtered": 25,
    "execution_path": ["query_parser", "permission_filter", "hybrid_search", "rerank"],
    "timing": 1.23
  }
}
```

### Admin API

**POST /api/admin/upload**

Upload and process a file.

Request (multipart/form-data):
- `file`: File to upload
- `uploaded_by`: User identifier (optional)

Response:
```json
{
  "success": true,
  "doc_id": "abc-123",
  "title": "uploaded-file.pdf",
  "message": "File processed successfully"
}
```

**GET /api/data-sources**

Get counts of indexed documents by source.

Response:
```json
{
  "total": 1232,
  "sources": {
    "box": 102,
    "slack": 6,
    "github": 15,
    "wiki": 99,
    "videos": 12,
    "images": 5
  }
}
```

---

## Configuration

### Qdrant Settings

Edit `backend/config/qdrant_config.py`:

```python
QDRANT_URL = "http://localhost:6333"
EMBEDDING_DIMENSION = 768
DEFAULT_SEARCH_LIMIT = 20
DEFAULT_SCORE_THRESHOLD = 0.5
```

### Collection Schema

EngineIQ uses the following Qdrant collections:
- `knowledge_base`: Primary search collection for all content
- `conversations`: Query tracking for pattern learning
- `expertise_map`: Expert finding based on contributions
- `knowledge_gaps`: Proactive gap detection

---

## Development

### Project Structure

```
EngineIQ/
├── backend/
│   ├── api/              # FastAPI server and routes
│   ├── services/         # Core services (Gemini, Qdrant, processors)
│   ├── agents/           # LangGraph agent system
│   ├── connectors/       # Data source connectors
│   ├── config/           # Configuration files
│   └── tests/            # Unit tests
├── scripts/              # Utility scripts for processing
├── docs/                 # Documentation
└── README.md
```

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Quality

```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type checking
mypy backend/
```

---

## Technology Stack

- **Backend**: Python 3.9+, FastAPI
- **AI/ML**: Google Gemini API (embeddings, vision, analysis)
- **Vector Database**: Qdrant
- **Agent Framework**: LangGraph
- **Processing**: PyPDF2, OpenCV, FFmpeg

---

## Demo Content

The system includes sample content for demonstration:
- LinkedIn School of SRE documentation (99 docs)
- Kubernetes wiki pages (3 docs)
- Sample PDFs, videos, and images
- Slack message samples
- GitHub code samples

---

## License

MIT License

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Support

For issues and questions, please open an issue on GitHub.

---

## Acknowledgments

- Google Gemini API for multimodal AI capabilities
- Qdrant for vector search infrastructure
- LinkedIn School of SRE for documentation samples
- Kubernetes documentation for wiki samples
