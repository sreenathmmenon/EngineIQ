# EngineIQ Demo Data Generator

Character-driven realistic data for all 5 demo scenarios.

## Quick Start

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Generate demo data
python backend/scripts/generate_demo_data.py
```

## What Gets Generated

### 50+ Slack Messages
- Priya's 2am deployment question → Sarah's detailed answer
- Database rollback questions (creates knowledge gap)
- Maria & Diego Spanish/English discussion
- Rajesh security audit request
- Confidential payments discussion (triggers approval)

### 20 GitHub Files
- deployment.sh script (Sarah)
- K8s manifests (Diego)
- Documentation (collaborative)
- Commits showing team contributions

### 15 Box Files
- Deployment runbooks (public)
- Architecture diagrams (Gemini Vision showcase)
- Q4 Financial Strategy (confidential - triggers approval)
- Contractor policies (third-party restricted)

### Expertise Profiles
- Sarah: 98.0 (deployment expert)
- Diego: 87.0 (K8s expert)
- Rajesh: 73.0 (security expert)
- Maria: 62.0 (auth expert)
- Priya: 45.0 (junior, learning)

### Knowledge Gaps
- Database rollback: 18 searches, quality 0.31 (HIGH)
- K8s resources: 12 searches, quality 0.45 (MEDIUM)

## Demo Queries

After generation, try:

1. `"How do I deploy hotfixes to production?"`
   - Shows Priya's scenario - timezone barrier broken

2. `"Who is the Kubernetes expert?"`
   - Shows Diego ranked #1 - invisible talent visible

3. `"Show me Q4 financial strategy"`
   - Triggers human-in-loop approval

## Output

Indexes ~40 items to Qdrant:
- knowledge_base: 40 documents
- expertise_map: 5 profiles
- knowledge_gaps: 2 gaps

Ready for live demo! 🚀
