# EngineIQ Demo Data Generation Skill

**Purpose:** Generate realistic, coherent demo data for EngineIQ hackathon demonstrations.

**When to use:** When preparing demo data that tells a compelling story and demonstrates all EngineIQ features.

---

## Overview

EngineIQ demo data must be:
- **Realistic**: Authentic engineering team content
- **Coherent**: Data tells a connected story
- **Comprehensive**: Covers all 5 demo scenarios
- **Diverse**: Multiple sources, content types, users
- **Triggering**: Activates human-in-loop and knowledge gaps

This skill teaches how to generate 100-200 documents that create a compelling narrative around a fictional engineering team working on "DeployBot" - a Kubernetes deployment automation tool.

---

## 1. Demo Scenario Specifications

### Scenario 1: Cross-Source Search

**Query:** "How do we deploy to production?"

**Expected Results:** Mix of sources showing deployment workflow

**Required Data:**
- ✅ Slack conversations in #devops channel about deployment
- ✅ GitHub deployment scripts (deploy.py, k8s manifests)
- ✅ Confluence runbook "Production Deployment Guide"
- ✅ Jira ticket "Automate production deployment"
- ✅ Box postmortem "Failed Deployment 2024-03-15"

**Story Arc:**
1. Initial question in Slack: "How do we safely deploy to prod?"
2. Discussion references GitHub PR with deployment script
3. Script uses kubectl commands documented in Confluence
4. Deployment failures led to Jira automation ticket
5. Postmortem in Box documents lessons learned

**Data Volume:** 15-20 documents across 5 sources

---

### Scenario 2: Multimodal Image Analysis

**Action:** Upload Kubernetes architecture diagram (PNG/JPG)

**Expected Results:** Related code and documentation

**Required Data:**
- ✅ Box/Drive: Architecture diagram (Kubernetes cluster with nodes, pods, ingress)
- ✅ GitHub: Code implementing the architecture (k8s manifests)
- ✅ Confluence: Architecture design doc referencing diagram
- ✅ Slack: Discussion about architecture decisions
- ✅ Jira: Epic for implementing the architecture

**Visual Content (Gemini Vision will analyze):**
- API server, etcd cluster
- Worker nodes with kubelet
- Load balancer → Ingress → Services → Pods
- Persistent volumes
- Monitoring stack (Prometheus, Grafana)

**Story Arc:**
1. Architecture diagram created during design phase
2. Design doc explains diagram components
3. Slack discussion about design tradeoffs
4. GitHub manifests implement the design
5. Jira epic tracks implementation progress

**Data Volume:** 8-10 documents + 1 diagram

---

### Scenario 3: Human-in-Loop (Sensitive Content)

**Query:** "Q4 revenue targets" or "Salary benchmarks"

**Expected Results:** Approval modal with flagged documents

**Required Data:**
- ✅ Confidential Google Docs: "Q4 2024 Revenue Forecast"
- ✅ Restricted Box file: "Engineering Salary Benchmarks.xlsx"
- ✅ Offshore-restricted Confluence: "Customer Contract Details"
- ✅ Third-party-restricted GitHub: "API Keys and Secrets"

**Sensitivity Markers:**
```python
{
    "permissions": {
        "sensitivity": "confidential",  # Triggers approval
        "offshore_restricted": True,     # Blocks offshore users
        "third_party_restricted": True   # Blocks vendors
    }
}
```

**PII Examples:**
- Employee SSNs (redacted in demo)
- Customer email addresses
- Credit card numbers (test data)

**Story Arc:**
1. User searches for financial/salary info
2. System finds 5 documents (3 confidential, 2 restricted)
3. Approval modal appears immediately
4. Shows what's flagged and why
5. Manager approves → results appear

**Data Volume:** 5-8 sensitive documents

---

### Scenario 4: Expertise Finding

**Query:** "Who's the Kubernetes expert?"

**Expected Results:** Ranked experts with evidence

**Required Data (for Alice as top expert):**
- ✅ **GitHub**: 15 commits to kubernetes/ directory
  - Action: "authored" (score: 2.0 × 15 = 30)
- ✅ **Slack**: 8 answered questions in #kubernetes channel
  - Action: "answered" (score: 1.5 × 8 = 12)
- ✅ **Confluence**: Authored 3 Kubernetes guides
  - Action: "authored" (score: 3.0 × 3 = 9)
- ✅ **Jira**: Resolved 5 kubernetes-related issues
  - Action: "resolved" (score: 1.0 × 5 = 5)
- ✅ **GitHub PRs**: Reviewed 6 kubernetes pull requests
  - Action: "reviewed" (score: 1.5 × 6 = 9)

**Total Score:** 30 + 12 + 9 + 5 + 9 = **65 points**

**Other Experts (for comparison):**
- **Bob**: 40 points (strong in Docker, moderate in k8s)
- **Charlie**: 25 points (dabbles in k8s, not expert)

**Evidence Display:**
```
Alice (Score: 65)
  - Authored k8s/deployment.py (GitHub)
  - Answered "How to scale pods?" (#kubernetes Slack)
  - Wrote "K8s Best Practices" (Confluence)
  - Resolved PROD-123: Pod crash loop (Jira)
  - Reviewed PR #456: Horizontal pod autoscaling (GitHub)
```

**Story Arc:**
1. Alice consistently contributes k8s content
2. Contributions span multiple sources (not siloed)
3. Recent activity (within 30 days) keeps score high
4. Bob and Charlie provide contrast for ranking

**Data Volume:** 40-50 contributions across sources

---

### Scenario 5: Knowledge Gap Detection

**Query Pattern:** "How to rollback database migrations?"

**Expected Results:** Gap dashboard showing high-priority gap

**Required Data:**
- ✅ **18 similar queries** in conversations collection
  - 12 different users searched variations
  - Queries within 7-day window
  - Average result score: 0.32 (poor)
  - Average user rating: 2.1 / 5 stars

- ✅ **Existing docs** (but inadequate):
  - Confluence: "Database Schema Guide" (mentions migrations briefly)
  - GitHub: migration_tool.py (code but no docs)
  - Slack: 2 threads asking about rollbacks (no clear answers)

- ✅ **Gap record:**
```python
{
    "query_pattern": "How to rollback database migrations?",
    "search_count": 18,
    "unique_users": ["alice", "bob", "charlie", "diana", "eve", ...],
    "avg_result_score": 0.32,
    "first_detected": 5_days_ago,
    "last_searched": 1_hour_ago,
    "priority": "high",  # >15 searches, >5 users
    "suggested_action": "Create runbook: Database Migration Rollback Procedures",
    "assigned_to": "alice",  # DB expert
    "status": "detected"
}
```

**Dashboard Display:**
```
Knowledge Gaps - High Priority

1. Database Migration Rollback [HIGH]
   - 18 searches by 12 users
   - Avg quality: 32% (poor)
   - Suggested: Create runbook
   - Assign to: Alice (DB expert)
   [Approve] [Dismiss]

2. Kubernetes Autoscaling Configuration [MEDIUM]
   - 11 searches by 6 users
   - Avg quality: 45%
   ...
```

**Story Arc:**
1. Multiple engineers struggle with db rollbacks
2. No clear documentation exists
3. System detects pattern over 7 days
4. Suggests creating documentation
5. Recommends Alice (DB expert) as author

**Data Volume:** 20-30 query records, 2-3 gaps

---

## 2. Realistic Content Patterns

### Slack Messages

**Patterns:**
- Technical questions and answers
- Code snippets in ```blocks```
- Thread discussions (parent + 3-5 replies)
- Reactions (👍 ✅ 🚀)
- @mentions of users
- Links to GitHub PRs, Jira tickets
- Incident response threads
- Retrospective discussions

**Example Thread:**
```
#devops | alice | 2024-03-15 14:32
How do we safely deploy to production? I saw the deploy.py script but not sure about the rollback process.

  bob | 14:35
  Check out PR #456 - I added rollback logic there
  https://github.com/company/deploybot/pull/456

  charlie | 14:38
  We also have a runbook in Confluence:
  https://wiki.company.com/production-deployment

  alice | 14:42
  Perfect! One question - do we run migrations before or after deployment?

  bob | 14:45
  After! Migrations are in a separate step. See deploy.py line 123
  ```python
  run_migrations()
  deploy_containers()
  run_health_checks()
  ```
```

**Channels:**
- #devops - Deployment, infrastructure
- #kubernetes - K8s specific discussions
- #incidents - Production issues
- #engineering - General tech discussions
- #database - DB migrations, performance

---

### GitHub Content

**Code Files:**
- Realistic Python/JavaScript/YAML
- Proper structure (imports, functions, comments)
- Semantic meaning (Gemini will analyze)

**Example: deployment/deploy.py**
```python
"""
DeployBot production deployment script.

Handles Docker builds, Kubernetes deployments, and health checks.
"""

import subprocess
import sys
from typing import Optional

def validate_version(version: str) -> bool:
    """Ensure version follows semver pattern."""
    import re
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))

def build_docker_image(app_name: str, version: str):
    """Build and tag Docker image."""
    print(f"Building {app_name}:{version}...")
    subprocess.run([
        "docker", "build",
        "-t", f"{app_name}:{version}",
        "-t", f"{app_name}:latest",
        "."
    ], check=True)

def deploy_to_kubernetes(app_name: str, version: str):
    """Update Kubernetes deployment with new version."""
    print(f"Deploying {app_name}:{version} to k8s...")
    subprocess.run([
        "kubectl", "set", "image",
        f"deployment/{app_name}",
        f"{app_name}={app_name}:{version}"
    ], check=True)

def run_health_checks() -> bool:
    """Verify deployment health."""
    # Check pod status, endpoint health, etc.
    return True

def main(app_name: str, version: str):
    if not validate_version(version):
        print("Invalid version format. Use semver: X.Y.Z")
        sys.exit(1)

    build_docker_image(app_name, version)
    deploy_to_kubernetes(app_name, version)

    if run_health_checks():
        print("✓ Deployment successful!")
    else:
        print("✗ Health checks failed. Rolling back...")
        # Rollback logic here

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

**Pull Requests:**
- Title: "Add automated rollback on deployment failure"
- Description: Problem, solution, testing
- Comments: Code review discussions
- Status: merged/open/closed

**Issues:**
- Title: Clear problem statement
- Labels: bug, enhancement, documentation
- Assignee, milestone
- Comments tracking progress

---

### Box/Drive Documents

**PDF Content (Gemini will parse):**
- Postmortems: "Production Outage 2024-03-15"
  - Timeline of events
  - Root cause analysis
  - Action items

- Architecture docs: "DeployBot System Design"
  - System components
  - Data flow diagrams
  - Technology stack

- Runbooks: "Kubernetes Incident Response"
  - Step-by-step procedures
  - Common issues and solutions
  - Escalation paths

**Images (Gemini Vision will analyze):**
- Architecture diagrams
- Network topology
- Database schema
- Deployment pipeline flow
- Monitoring dashboards

---

### Jira Issues

**Issue Types:**
- Epic: "Automate Kubernetes Deployments"
- Story: "As a developer, I want automated rollbacks"
- Task: "Write deployment runbook"
- Bug: "Deployment fails on migration errors"

**Workflow:**
- To Do → In Progress → Code Review → Testing → Done

**Example Issue:**
```
PROD-123: Pod crash loop after deployment

Type: Bug
Priority: High
Assignee: alice
Labels: kubernetes, production, urgent

Description:
After deploying version 2.3.1, pods are crash looping with OOMKilled status.
Memory limit might be too low.

Comments:
  bob | 10:15
  Checked logs - heap dump shows 512MB isn't enough. Recommend 1GB.

  alice | 10:30
  Updated deployment.yaml to 1GB. Testing in staging now.

  alice | 11:00
  ✓ Fixed! Deploying to prod.

Status: Done
```

---

### Confluence Pages

**Page Types:**
- Runbooks: Step-by-step operational guides
- Architecture docs: System design, diagrams
- Meeting notes: Engineering sync notes
- How-to guides: "How to Deploy to Production"
- Team docs: On-call rotation, escalation

**Example Page: "Production Deployment Guide"**
```markdown
# Production Deployment Guide

## Prerequisites
- kubectl configured for prod cluster
- Docker image built and pushed
- All tests passing in CI

## Deployment Steps

1. **Validate Version**
   ```bash
   ./scripts/validate-version.sh v2.3.1
   ```

2. **Run Deployment Script**
   ```bash
   python deployment/deploy.py deploybot 2.3.1
   ```

3. **Monitor Health**
   - Check Grafana: https://grafana.company.com/deploybot
   - Watch pod status: `kubectl get pods -n production`

4. **Rollback if Needed**
   ```bash
   kubectl rollout undo deployment/deploybot
   ```

## Common Issues

### Pods CrashLooping
- Check memory limits in deployment.yaml
- Review logs: `kubectl logs <pod-name>`

### Database Migration Errors
- Verify migration order
- Check for conflicting schema changes

## Related Links
- GitHub: deployment scripts
- Jira: PROD-123 (deployment automation)
- Slack: #devops channel
```

---

## 3. Creating Coherent Stories

### The DeployBot Narrative

**Fictional Company:** TechCorp
**Product:** DeployBot - Kubernetes deployment automation
**Team:** 8 engineers (alice, bob, charlie, diana, eve, frank, grace, henry)

**Timeline (Last 30 Days):**

**Week 1: Architecture Design**
- Grace creates architecture diagram in Box
- Team discusses in Slack #engineering
- Alice writes design doc in Confluence
- Bob creates Epic in Jira: "Build DeployBot v1.0"

**Week 2: Initial Implementation**
- Alice commits deploy.py to GitHub
- Bob implements Docker build pipeline
- Charlie adds Kubernetes manifests
- Code reviews happen via GitHub PRs

**Week 3: First Production Deployment**
- Diana deploys to staging successfully
- Team discusses deployment process in Slack #devops
- Eve documents runbook in Confluence
- First prod deployment FAILS

**Week 4: Incident Response & Improvement**
- Production incident (pods crash looping)
- Slack #incidents channel - live debugging
- Alice fixes memory limits (GitHub commit)
- Post-mortem written in Box
- Jira tickets created for improvements
- Knowledge gap detected: rollback procedures

**Cross-References:**
- Slack discusses GitHub PR #456
- Confluence runbook links to GitHub scripts
- Jira ticket references Slack incident thread
- Box postmortem cites Confluence runbook gaps

---

### Character Consistency

**Alice (Senior Engineer - Kubernetes Expert)**
- Most active in k8s channels
- Writes most code in deployment/
- Authors Confluence guides
- Top expertise score: 65

**Bob (DevOps Engineer - Docker/CI Expert)**
- Active in #devops and #ci-cd
- Reviews most PRs
- Expertise in CI pipelines
- Score: 45 (secondary expert)

**Charlie (Full-Stack Developer)**
- Less k8s experience
- Asks questions, learns
- Contributes to application code
- Score: 25 (learning)

**Diana (Product Manager)**
- Owns Jira epics
- Asks high-level questions
- Not technical contributor
- No expertise score

---

## 4. Triggering Human-in-Loop Checkpoints

### Checkpoint 1: Sensitivity Levels

**Confidential Content:**
```python
# Q4 Revenue Forecast (Google Docs)
{
    "title": "Q4 2024 Revenue Targets - CONFIDENTIAL",
    "permissions": {
        "public": False,
        "teams": ["executive", "finance"],
        "sensitivity": "confidential",  # ⚠️ TRIGGERS APPROVAL
        "offshore_restricted": True,
        "third_party_restricted": True
    }
}
```

**Restricted Content:**
```python
# Salary Benchmarks (Box Excel)
{
    "title": "Engineering Salary Benchmarks 2024",
    "permissions": {
        "sensitivity": "restricted",  # ⚠️ TRIGGERS APPROVAL
        "teams": ["hr", "executive"],
        "offshore_restricted": True,
        "third_party_restricted": True
    }
}
```

**Internal Content (No Trigger):**
```python
# Regular Engineering Doc
{
    "title": "Kubernetes Deployment Guide",
    "permissions": {
        "sensitivity": "internal",  # ✓ No approval needed
        "teams": ["engineering"],
        "offshore_restricted": False,
        "third_party_restricted": False
    }
}
```

---

### Checkpoint 2: Offshore Restrictions

**User Types:**

**Regular Employee:**
```python
user = {
    "id": "alice",
    "teams": ["engineering"],
    "offshore": False,  # ✓ Can see offshore-restricted
    "third_party": False
}
```

**Offshore Contractor:**
```python
user = {
    "id": "contractor_raj",
    "teams": ["engineering"],
    "offshore": True,  # ✗ Blocked from offshore-restricted
    "third_party": False
}
```

**Documents to Restrict:**
- Customer contracts
- Financial data
- Source code (in some cases)
- API keys and secrets

---

### Checkpoint 3: PII Detection

**PII Patterns to Include:**
- Email addresses: `alice@company.com`
- Phone numbers: `(555) 123-4567`
- SSNs (redacted): `***-**-1234`
- Credit cards (test): `4111-1111-1111-1111`

**Detection Logic:**
```python
import re

def detect_pii(content: str) -> bool:
    """Detect if content contains PII"""
    patterns = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
    ]

    for pattern in patterns:
        if re.search(pattern, content):
            return True

    return False
```

---

## 5. Building Expertise Profiles

### Expertise Score Formula

```python
score = (
    (github_commits * 2.0) +
    (slack_answers * 1.5) +
    (confluence_authored * 3.0) +
    (jira_resolved * 1.0) +
    (code_reviews * 1.5)
) * recency_multiplier

# Recency multiplier
if days_since_contribution < 30:
    recency_multiplier = 1.0
elif days_since_contribution < 90:
    recency_multiplier = 0.8
else:
    recency_multiplier = 0.5
```

### Example: Alice's Kubernetes Expertise

**GitHub Commits (15 × 2.0 = 30)**
```
1. k8s/deployment.py - Initial deployment script
2. k8s/manifests/app.yaml - Application manifest
3. k8s/manifests/service.yaml - Service definition
4. k8s/rollback.py - Rollback automation
5. k8s/health_checks.py - Health check utilities
... (10 more commits)
```

**Slack Answers (8 × 1.5 = 12)**
```
1. "How to scale pods horizontally?" - Detailed answer
2. "Best practices for k8s secrets?" - Security guide
3. "Pod crash loop debugging?" - Step-by-step help
4. "Ingress vs LoadBalancer?" - Architecture advice
... (4 more answers)
```

**Confluence Docs (3 × 3.0 = 9)**
```
1. "Kubernetes Best Practices"
2. "Production Deployment Guide"
3. "Kubernetes Troubleshooting Runbook"
```

**Jira Issues (5 × 1.0 = 5)**
```
1. PROD-123: Pod crash loop - RESOLVED
2. PROD-145: Autoscaling config - RESOLVED
3. PROD-167: Ingress routing - RESOLVED
... (2 more)
```

**Code Reviews (6 × 1.5 = 9)**
```
1. PR #456: Deployment rollback logic - APPROVED
2. PR #489: Horizontal pod autoscaler - APPROVED
... (4 more)
```

**Total: 65 points** (all within last 30 days → recency = 1.0)

---

## 6. Creating Knowledge Gaps

### Gap Detection Algorithm

```python
def detect_gap(query_embedding, query_text, user_id):
    # Find similar queries
    similar_queries = qdrant.search(
        collection="conversations",
        vector=query_embedding,
        limit=20,
        score_threshold=0.8  # Very similar
    )

    if len(similar_queries) >= 10:
        avg_score = sum(q["top_result_score"] for q in similar_queries) / len(similar_queries)

        if avg_score < 0.4:  # Poor results
            # This is a knowledge gap!
            return create_gap_record(similar_queries, query_text)
```

### Example Gap: Database Migration Rollback

**18 Similar Queries:**
```
1. "How to rollback database migrations?" - Score: 0.28
2. "Undo database migration" - Score: 0.32
3. "Reverse migration in production" - Score: 0.35
4. "Migration rollback procedure" - Score: 0.30
5. "Failed migration recovery" - Score: 0.25
... (13 more with similar poor scores)
```

**Users:** alice, bob, charlie, diana, eve, frank, grace, henry, intern1, intern2, intern3, intern4

**Existing Docs (Inadequate):**
- Confluence: "Database Schema Guide" → Mentions migrations (1 paragraph)
- GitHub: `migration_tool.py` → Code but no usage docs
- Slack: 2 threads with partial answers

**Gap Record:**
```python
{
    "id": "gap_db_migration_rollback",
    "query_pattern": "How to rollback database migrations?",
    "search_count": 18,
    "unique_users": ["alice", "bob", "charlie", ...],  # 12 users
    "avg_result_score": 0.32,
    "avg_user_rating": 2.1,  # Out of 5
    "first_detected": 1710777600,  # 5 days ago
    "last_searched": 1711123200,   # 1 hour ago
    "priority": "high",  # Because 18 searches, 12 users
    "suggested_action": "Create runbook: Database Migration Rollback Procedures",
    "assigned_to": "alice",  # Found via expertise_map for "database"
    "status": "detected",
    "related_docs": [
        "confluence_db_schema_guide",
        "github_migration_tool_py"
    ]
}
```

### Other Gaps to Create

**Medium Priority:**
- "Kubernetes autoscaling configuration" - 11 searches, 6 users
- "CI/CD pipeline debugging" - 13 searches, 7 users

**Low Priority:**
- "Docker image optimization" - 8 searches, 4 users

---

## 7. Data Volume Guidelines

### Total: 150-200 Documents

**Slack: 60 messages**
- #devops: 20 messages (deployment discussions)
- #kubernetes: 15 messages (k8s specific)
- #incidents: 10 messages (production issues)
- #engineering: 10 messages (general)
- #database: 5 messages (DB topics)

**GitHub: 35 files + commits**
- Code files: 20 (Python, YAML, shell scripts)
- Pull requests: 8 (with reviews and comments)
- Issues: 7 (bugs, features, tasks)

**Box/Drive: 25 documents**
- PDFs: 15 (postmortems, runbooks, designs)
- Images: 5 (architecture diagrams)
- Spreadsheets: 3 (data, metrics)
- Presentations: 2 (planning, retrospectives)

**Jira: 15 issues**
- Epics: 2
- Stories: 6
- Tasks: 4
- Bugs: 3

**Confluence: 10 pages**
- Runbooks: 4
- Architecture docs: 3
- Meeting notes: 2
- Team docs: 1

**Other Collections:**
- Conversations: 30 query records
- Expertise entries: 50 (across 8 users)
- Knowledge gaps: 3

---

## 8. Generation Strategy

### Phase 1: Define Characters & Timeline

```python
USERS = {
    "alice": {
        "role": "Senior Engineer",
        "expertise": ["kubernetes", "python", "deployment"],
        "activity_level": "high"
    },
    "bob": {
        "role": "DevOps Engineer",
        "expertise": ["docker", "ci-cd", "infrastructure"],
        "activity_level": "high"
    },
    "charlie": {
        "role": "Full-Stack Developer",
        "expertise": ["javascript", "react", "api"],
        "activity_level": "medium"
    },
    # ... more users
}

TIMELINE = {
    "week_1": "Architecture & Design",
    "week_2": "Initial Implementation",
    "week_3": "First Deployment",
    "week_4": "Incident & Improvement"
}
```

---

### Phase 2: Generate Core Content

```python
# 1. Create base documents for each source
slack_messages = generate_slack_threads(users, timeline)
github_files = generate_github_repository(users)
confluence_pages = generate_confluence_docs(users)
jira_issues = generate_jira_workflow(users)
box_documents = generate_box_files(users)

# 2. Add cross-references
cross_reference_content(slack_messages, github_files, jira_issues)

# 3. Generate embeddings (via Gemini)
embed_all_content(all_documents)
```

---

### Phase 3: Index to Qdrant

```python
# Index to knowledge_base
qdrant.upsert("knowledge_base", knowledge_points)

# Build expertise map
qdrant.upsert("expertise_map", expertise_points)

# Seed conversations for gap detection
qdrant.upsert("conversations", conversation_points)

# Create initial gaps
qdrant.upsert("knowledge_gaps", gap_points)
```

---

## 9. Complete Examples

See `examples/` directory for:
- `generate_slack.py` - Realistic Slack conversations
- `generate_github.py` - Code repository with PRs
- `generate_box.py` - Documents and diagrams
- `generate_jira.py` - Issue tracking workflow
- `generate_confluence.py` - Wiki documentation
- `full_demo_data.py` - Complete 200-doc dataset
- `verify_scenarios.py` - Test all 5 demo scenarios

---

## Summary

This skill teaches how to generate realistic demo data that:
- ✅ Tells a coherent story (DeployBot narrative)
- ✅ Covers all 5 demo scenarios
- ✅ Triggers human-in-loop checkpoints
- ✅ Builds expertise profiles
- ✅ Creates knowledge gaps
- ✅ Cross-references between sources
- ✅ Uses realistic timestamps and user patterns
- ✅ Totals 150-200 high-quality documents

The data enables flawless demo execution and showcases all EngineIQ features.
