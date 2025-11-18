# EngineIQ Custom Skills Summary

Three comprehensive skills for building EngineIQ's AI-powered knowledge intelligence platform.

---

## 1. engineiq-connector-builder

**Purpose:** Build connectors following a standard pattern for any data source.

**Location:** `.claude/skills/engineiq-connector-builder/`

**What it teaches:**
- ✅ BaseConnector abstract class pattern
- ✅ Authentication (OAuth2, API tokens, basic auth)
- ✅ Content extraction for all file types (text, code, PDFs, images, video, audio)
- ✅ Gemini integration for embeddings (text-embedding-004)
- ✅ Qdrant indexing with proper payload structure
- ✅ Permission handling (public, teams, sensitivity, offshore/third-party)
- ✅ Error handling and retry logic
- ✅ Webhook setup for real-time updates
- ✅ Testing with mocks

**Key files:**
- `skill.md` - Complete connector pattern (9 sections)
- `examples/slack_connector.py` - Full Slack implementation
- `examples/github_connector.py` - Full GitHub implementation
- `examples/test_connector.py` - Testing patterns

**Use when:** Building any connector (Slack, GitHub, Box, Jira, etc.)

---

## 2. engineiq-qdrant-operations

**Purpose:** Master all Qdrant vector database operations.

**Location:** `.claude/skills/engineiq-qdrant-operations/`

**What it teaches:**
- ✅ All 4 collection schemas (knowledge_base, conversations, expertise_map, knowledge_gaps)
- ✅ Hybrid search (vector similarity + metadata filters)
- ✅ Batch indexing with performance optimization
- ✅ Permission-aware filtering (automatic security)
- ✅ Scroll API for large result sets (>100 results)
- ✅ Recommendation engine (similar documents, expert finding)
- ✅ Performance optimization (indexing, HNSW tuning)
- ✅ Complete error handling

**Key files:**
- `skill.md` - Complete Qdrant patterns (8 sections)
- `examples/qdrant_service.py` - Production-ready service class (600+ lines)
- `examples/search_examples.py` - 15+ search patterns
- `examples/indexing_examples.py` - 12+ indexing patterns

**Use when:** Implementing any Qdrant operation (search, index, recommend)

---

## 3. engineiq-demo-data

**Purpose:** Generate realistic, coherent demo data for hackathon presentations.

**Location:** `.claude/skills/engineiq-demo-data/`

**What it teaches:**
- ✅ Demo scenario specifications (all 5 scenarios)
- ✅ Realistic content patterns for each source
- ✅ Creating coherent stories (DeployBot narrative)
- ✅ Triggering human-in-loop checkpoints
- ✅ Building expertise profiles (scoring formula)
- ✅ Creating knowledge gaps (detection algorithm)
- ✅ Data volume guidelines (150-200 docs)
- ✅ Complete generation examples

**Key files:**
- `skill.md` - Complete demo data patterns (9 sections)
- `examples/generate_slack.py` - Realistic Slack conversations
- `examples/full_demo_data.py` - Complete dataset generator

**Use when:** Preparing demo data that showcases all EngineIQ features

---

## How to Use These Skills

### Reference a Skill

When you need to implement something covered by a skill, simply say:

```
"Use the engineiq-connector-builder skill to create a Jira connector"
```

I will then follow the exact patterns from that skill.

### Combine Skills

For complex tasks, reference multiple skills:

```
"Use engineiq-connector-builder to create a Confluence connector,
then use engineiq-qdrant-operations to index the data"
```

### Proactive Usage

I will automatically use these skills when appropriate:
- Building connectors → engineiq-connector-builder
- Qdrant operations → engineiq-qdrant-operations
- Demo data → engineiq-demo-data

---

## Skill Coverage

### EngineIQ Build Plan Alignment

These skills cover the core implementation patterns from `BUILD_PLAN.md`:

**Phase 1: Foundation**
- ✅ Qdrant setup → engineiq-qdrant-operations
- ✅ Gemini service → engineiq-connector-builder (Section 4)
- ✅ BaseConnector → engineiq-connector-builder (Section 1)

**Phase 2: Core Connectors**
- ✅ Slack → engineiq-connector-builder (example)
- ✅ GitHub → engineiq-connector-builder (example)
- ✅ Box → engineiq-connector-builder (pattern)

**Phase 3: Additional Connectors**
- ✅ Drive, Jira, Confluence → engineiq-connector-builder (pattern)

**Phase 4: Agent System**
- ✅ Qdrant operations → engineiq-qdrant-operations
- ✅ Permission filtering → engineiq-qdrant-operations (Section 2)

**Phase 5: Frontend**
- (Not covered by skills - standard React patterns)

**Phase 6: Demo Data**
- ✅ All demo scenarios → engineiq-demo-data

---

## Quick Reference

### I need to...

**Build a connector for a new source**
→ Use `engineiq-connector-builder`

**Search with permissions**
→ Use `engineiq-qdrant-operations` Section 2

**Find similar documents**
→ Use `engineiq-qdrant-operations` Section 5

**Batch index 1000 documents**
→ Use `engineiq-qdrant-operations` Section 3

**Generate realistic Slack messages**
→ Use `engineiq-demo-data` Section 2

**Create expertise profiles**
→ Use `engineiq-demo-data` Section 5

**Trigger human-in-loop**
→ Use `engineiq-demo-data` Section 4

**Detect knowledge gaps**
→ Use `engineiq-demo-data` Section 6

---

## File Locations

```
.claude/skills/
├── SKILLS_SUMMARY.md                    # This file
├── engineiq-connector-builder/
│   ├── README.md
│   ├── skill.md
│   └── examples/
│       ├── slack_connector.py
│       ├── github_connector.py
│       └── test_connector.py
├── engineiq-qdrant-operations/
│   ├── README.md
│   ├── skill.md
│   └── examples/
│       ├── qdrant_service.py
│       ├── search_examples.py
│       └── indexing_examples.py
└── engineiq-demo-data/
    ├── README.md
    ├── skill.md
    └── examples/
        ├── generate_slack.py
        └── full_demo_data.py
```

---

## Success Metrics

With these skills, you can:

✅ Build any connector in 3-6 hours following standard pattern
✅ Implement all Qdrant operations correctly on first try
✅ Generate 150-200 realistic demo documents in <1 hour
✅ Cover all 5 demo scenarios comprehensively
✅ Achieve target scores:
  - Qdrant Challenge: 95/100
  - Gemini Challenge: 90/100
  - Opus Challenge: High Impact

---

## Next Steps

1. **Review skills** - Read each README.md for quick start
2. **Reference as needed** - Use skills during implementation
3. **Customize** - Adapt patterns for specific needs
4. **Iterate** - Update skills as patterns evolve

---

**All three skills are ready to use! 🚀**
