# EngineIQ Demo Data Generation Skill

A comprehensive skill for generating realistic, coherent demo data for EngineIQ hackathon demonstrations.

## What This Skill Teaches

This skill provides everything you need to generate demo data that:
- ✅ Tells a compelling story (DeployBot narrative)
- ✅ Covers all 5 demo scenarios
- ✅ Creates realistic content across all sources
- ✅ Triggers human-in-loop checkpoints
- ✅ Builds expertise profiles
- ✅ Detects knowledge gaps
- ✅ Cross-references between sources
- ✅ Uses realistic timestamps and interactions

## Quick Start

### 1. Read the Main Skill Documentation
Start with `skill.md` for complete demo data patterns.

### 2. Review Example Generators
- `examples/generate_slack.py` - Slack conversations (60 messages)
- `examples/full_demo_data.py` - Complete dataset generator

### 3. Generate Demo Data
```python
from full_demo_data import DemoDataGenerator

generator = DemoDataGenerator()
demo_data = generator.generate_all_demo_data()

# Returns:
# {
#   "knowledge_base": [...],  # 150-200 documents
#   "expertise_map": [...],   # 50 entries
#   "conversations": [...],   # 30 queries
#   "knowledge_gaps": [...]   # 3 gaps
# }
```

## File Structure

```
engineiq-demo-data/
├── README.md                       # This file
├── skill.md                        # Complete documentation
└── examples/
    ├── generate_slack.py          # Slack message generator
    └── full_demo_data.py          # Complete dataset generator
```

## The DeployBot Story

All demo data tells a coherent story about:

**Company:** TechCorp
**Product:** DeployBot - Kubernetes deployment automation
**Team:** 8 engineers working over 4 weeks

**Timeline:**
- **Week 1:** Architecture design (diagrams, discussions)
- **Week 2:** Implementation (code commits, PRs)
- **Week 3:** First production deployment (success + failure)
- **Week 4:** Incident response & improvements

This creates natural cross-references:
- Slack discusses GitHub PRs
- Confluence runbooks link to scripts
- Jira tickets reference incidents
- Box postmortems cite documentation gaps

## 5 Demo Scenarios

### Scenario 1: Cross-Source Search
**Query:** "How do we deploy to production?"
**Results:** 15-20 documents from Slack, GitHub, Confluence, Jira, Box

Shows EngineIQ finding relevant content across all sources.

### Scenario 2: Multimodal Image Analysis
**Action:** Upload Kubernetes architecture diagram
**Results:** Related code and documentation

Demonstrates Gemini Vision analyzing diagrams and finding related technical content.

### Scenario 3: Human-in-Loop
**Query:** "Q4 revenue targets"
**Results:** Approval modal with flagged sensitive documents

Showcases permission filtering and human approval workflow.

### Scenario 4: Expertise Finding
**Query:** "Who's the Kubernetes expert?"
**Results:** Ranked experts with evidence

Alice (65 pts) > Bob (45 pts) > Charlie (25 pts) based on contributions.

### Scenario 5: Knowledge Gap Detection
**Pattern:** 18 searches for "How to rollback database migrations?"
**Results:** Gap dashboard showing high-priority missing documentation

Demonstrates proactive knowledge management.

## Data Volume

**Total: 150-200 documents**

- **Slack:** 60 messages across 5 channels
- **GitHub:** 35 files + PRs + issues
- **Box/Drive:** 25 documents (PDFs, images, spreadsheets)
- **Jira:** 15 issues (epics, stories, bugs)
- **Confluence:** 10 wiki pages
- **Expertise:** 50 contribution records
- **Conversations:** 30 query records
- **Knowledge Gaps:** 3 detected gaps

## Character Profiles

### Alice (Senior Engineer - K8s Expert)
- **Expertise Score:** 65
- **Contributions:**
  - 15 GitHub commits to k8s/
  - 8 Slack answers in #kubernetes
  - 3 Confluence guides authored
  - 5 Jira issues resolved
  - 6 PR reviews
- **Activity:** High (last contribution 3 days ago)

### Bob (DevOps Engineer)
- **Expertise Score:** 45
- **Focus:** Docker, CI/CD pipelines
- **Activity:** High

### Charlie (Full-Stack Developer)
- **Expertise Score:** 25
- **Learning K8s:** Asks questions, moderate contributions
- **Activity:** Medium

## Triggering Human-in-Loop

### Sensitivity Levels

**Confidential** (triggers approval):
```python
"permissions": {
    "sensitivity": "confidential",  # ⚠️ APPROVAL REQUIRED
    "teams": ["executive", "finance"]
}
```

**Restricted** (triggers approval):
```python
"permissions": {
    "sensitivity": "restricted",  # ⚠️ APPROVAL REQUIRED
    "offshore_restricted": True,
    "third_party_restricted": True
}
```

**Internal** (no approval):
```python
"permissions": {
    "sensitivity": "internal",  # ✓ No approval needed
    "teams": ["engineering"]
}
```

### Sensitive Documents

- Q4 Revenue Forecast (confidential)
- Salary Benchmarks (restricted)
- Customer Contracts (offshore-restricted)
- API Keys (third-party-restricted)

## Building Expertise Profiles

### Scoring Formula

```python
score = (
    (github_commits * 2.0) +
    (slack_answers * 1.5) +
    (confluence_authored * 3.0) +
    (jira_resolved * 1.0) +
    (code_reviews * 1.5)
) * recency_multiplier
```

### Example: Alice's K8s Expertise

| Source     | Action    | Count | Score/Each | Total |
|------------|-----------|-------|------------|-------|
| GitHub     | authored  | 15    | 2.0        | 30    |
| Slack      | answered  | 8     | 1.5        | 12    |
| Confluence | authored  | 3     | 3.0        | 9     |
| Jira       | resolved  | 5     | 1.0        | 5     |
| GitHub     | reviewed  | 6     | 1.5        | 9     |

**Total:** 65 points × 1.0 (recent) = **65**

## Creating Knowledge Gaps

### Detection Algorithm

```python
# Detect gap if:
if (
    search_count >= 10 and          # Many searches
    avg_result_score < 0.4 and      # Poor results
    time_window <= 7 days           # Recent pattern
):
    priority = "high" if unique_users > 5 else "medium"
    suggest_documentation()
```

### Example Gap: DB Migration Rollback

- **18 searches** by 12 different users
- **Average score:** 0.32 (poor)
- **Time window:** 7 days
- **Priority:** HIGH
- **Suggestion:** "Create runbook: Database Migration Rollback Procedures"
- **Assigned to:** Alice (database expert)

## Realistic Content Patterns

### Slack Messages

Features:
- Threaded discussions (parent + 3-5 replies)
- Code snippets in ```blocks```
- @mentions
- Links to GitHub/Jira
- Reactions (👍 ✅ 🚀)
- Natural conversation flow

### GitHub Code

Features:
- Proper structure (imports, functions, docstrings)
- Semantic meaning (Gemini will analyze)
- Realistic Python/YAML
- Comments explaining logic

### Confluence Pages

Features:
- Runbooks with step-by-step procedures
- Architecture documentation
- Code examples
- Links to related resources

### Jira Issues

Features:
- Clear titles and descriptions
- Workflow states (To Do → Done)
- Comments tracking progress
- Labels and assignees

## Cross-References

Demo data includes natural cross-references:

1. **Slack → GitHub**
   - "Check out PR #456" with actual link

2. **Confluence → GitHub**
   - Runbook references deploy.py script

3. **Jira → Slack**
   - Issue mentions Slack incident thread

4. **Box → Confluence**
   - Postmortem cites runbook gaps

5. **GitHub → Jira**
   - Commit message references PROD-123

## Using the Generators

### Generate Slack Messages

```python
from generate_slack import generate_all_slack_messages

messages = generate_all_slack_messages()
# Returns 60+ messages across channels

# Breakdown:
# #devops: 20 (deployment discussions)
# #kubernetes: 15 (k8s specific)
# #incidents: 10 (production issues)
# #engineering: 10 (general)
# #database: 5 (DB topics)
```

### Generate Complete Dataset

```python
from full_demo_data import DemoDataGenerator

generator = DemoDataGenerator()
data = generator.generate_all_demo_data()

# Includes all 5 scenarios:
# ✓ Cross-source search data
# ✓ Multimodal image data
# ✓ Sensitive content data
# ✓ Expertise profiles
# ✓ Knowledge gap data
```

### Index to Qdrant

```python
from qdrant_service import QdrantService
from gemini_service import GeminiService

# Initialize services
qdrant = QdrantService(url="...")
gemini = GeminiService(api_key="...")

# Generate embeddings
for doc in data["knowledge_base"]:
    doc["vector"] = gemini.generate_embedding(doc["content"])

# Index to Qdrant
qdrant.upsert("knowledge_base", data["knowledge_base"])
qdrant.upsert("expertise_map", data["expertise_map"])
qdrant.upsert("conversations", data["conversations"])
qdrant.upsert("knowledge_gaps", data["knowledge_gaps"])
```

## Verifying Demo Scenarios

After indexing, test each scenario:

### Test Scenario 1
```python
# Search: "How do we deploy to production?"
results = qdrant.search(
    "knowledge_base",
    query_embedding,
    limit=20
)

# Should return:
# - Slack deployment discussion
# - GitHub deploy.py
# - Confluence runbook
# - Jira automation ticket
# - Box postmortem
```

### Test Scenario 2
```python
# Upload architecture diagram
# Gemini Vision analyzes it
# Search with diagram embedding

results = qdrant.search(
    "knowledge_base",
    diagram_embedding,
    limit=10
)

# Should return:
# - GitHub k8s manifests
# - Confluence architecture doc
# - Slack architecture discussion
```

### Test Scenario 3
```python
# Search: "Q4 revenue targets"
user = {"teams": ["engineering"], "offshore": False}

results = qdrant.search_with_permissions(
    query_embedding,
    user,
    limit=20
)

# Should trigger approval for:
# - Q4 Revenue Forecast (confidential)
# - Salary Benchmarks (restricted)
```

### Test Scenario 4
```python
# Search: "kubernetes expert"
experts = qdrant.find_experts(
    kubernetes_embedding,
    limit=5
)

# Should return:
# 1. alice (65 pts)
# 2. bob (45 pts)
# 3. charlie (25 pts)
```

### Test Scenario 5
```python
# Check knowledge gaps
gaps = qdrant.scroll(
    "knowledge_gaps",
    scroll_filter=Filter(
        must=[FieldCondition(key="priority", match="high")]
    )
)

# Should return:
# - DB migration rollback (18 searches, priority: high)
```

## Customization

### Add More Users
```python
USERS["isabel"] = {
    "role": "Data Engineer",
    "expertise": ["spark", "airflow", "python"]
}
```

### Create New Scenarios
```python
def generate_custom_scenario():
    # Your scenario logic
    return documents
```

### Adjust Data Volume
```python
# More Slack messages
generate_slack_messages(count=100)

# Fewer GitHub files
generate_github_content(max_files=15)
```

## Best Practices

1. **Keep it coherent** - Data should tell a connected story
2. **Use realistic timestamps** - Spread over 30 days
3. **Cross-reference naturally** - Don't force connections
4. **Vary content quality** - Not all docs are perfect
5. **Include edge cases** - Sensitive content, poor results, etc.
6. **Test all scenarios** - Verify every demo works

## Troubleshooting

### Issue: Scenario not triggering
- ✅ Check document permissions match requirements
- ✅ Verify embeddings generated correctly
- ✅ Ensure proper indexing to Qdrant

### Issue: No knowledge gaps detected
- ✅ Need 10+ similar queries
- ✅ Avg result score must be < 0.4
- ✅ Queries must be within 7-day window

### Issue: Expertise scores too low
- ✅ Add more contributions
- ✅ Use higher-value actions (authored docs = 3.0)
- ✅ Ensure recent activity (< 30 days)

## Resources

- **Main Build Plan**: `../../../BUILD_PLAN.md`
- **Demo Requirements**: BUILD_PLAN.md Section 10
- **Skill Documentation**: `skill.md`
- **Example Generators**: `examples/`

---

**Ready to generate demo data?** Start with `skill.md` for the complete narrative! 🎬
