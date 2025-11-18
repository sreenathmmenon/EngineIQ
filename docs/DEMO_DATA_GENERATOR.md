# EngineIQ Demo Data Generator

## Overview

Comprehensive character-driven demo data generator that creates realistic data for all 5 demo scenarios from `DEMO_SCRIPT.md`.

**File:** `backend/scripts/generate_demo_data.py` (550+ lines)

## Characters

1. **Priya Sharma** - Junior Engineer, Bangalore, India (offshore)
2. **Sarah Chen** - Senior Engineer/Manager, San Francisco, USA
3. **Diego Fernández** - Staff Engineer (K8s Expert), Buenos Aires, Argentina
4. **Maria Gonzalez** - Engineer, Mendoza, Argentina
5. **Rajesh Patel** - Security Contractor, Mumbai, India (third-party)

## Generated Data

### Slack Data (50+ messages)
**Channels:**
- `#engineering` - General engineering discussions
- `#kubernetes` - K8s troubleshooting
- `#security` - Security audits
- `#confidential-payments` - Confidential discussions (triggers human-in-loop)

**Key Scenarios:**

#### Scenario 1: Priya's 2am Production Deployment
- Priya asks: "How do I deploy hotfixes to production safely?"
- Timestamp: 2am Bangalore time (SF team asleep)
- Sarah responds 15 minutes later with detailed guide including bash scripts
- Priya successfully deploys hotfix solo - "I feel like a real engineer now!"
- Demonstrates: **Breaking timezone barriers**

#### Scenario 2: Database Migration Rollback (Knowledge Gap)
- 6 different engineers ask similar questions over 2 weeks
- Creates knowledge gap detection trigger
- Low average result quality (0.31)
- Suggests: Diego should write comprehensive runbook
- Demonstrates: **Proactive burnout prevention**

#### Scenario 3: Maria & Diego - Spanish to English
- Maria posts in Spanish: "¿Alguien puede ayudarme con un problema de autenticación?"
- Diego responds in Spanish, then English with technical solution
- Includes JWT secret rotation fix with kubectl commands
- Demonstrates: **Breaking language barriers**

#### Scenario 4: Rajesh Security Audit
- Rajesh requests access to RBAC policies and network configs
- Sarah grants read access with proper documentation
- For production credentials, requires written approval
- Demonstrates: **Ethical AI with appropriate gatekeeping**

#### Scenario 5: Confidential Payment Migration
- Sarah posts confidential payment system migration details
- Stripe integration, $1.2M budget, Q1 2025 timeline
- Diego adds monitoring configuration
- Channel triggers human-in-loop approval
- Demonstrates: **Security and compliance**

### GitHub Data (20 files)
**Repositories:**
- `backend-api` - Main application code
- `k8s-configs` - Kubernetes configurations  
- `deployment-scripts` - Deployment automation

**Key Files:**
1. `scripts/deploy.sh` - Sarah's deployment script (referenced in Slack answer)
2. `k8s-configs/production/api-deployment.yaml` - Diego's K8s manifests
3. `docs/DEPLOYMENT.md` - Deployment documentation
4. Commits from all team members showing collaborative work

### Box Data (15 files)
**Folders:**
- `/Engineering/Docs/` - Public documentation
- `/Engineering/Architecture/` - Diagrams (Gemini Vision showcase)
- `/Finance/Confidential/` - Confidential files (triggers human-in-loop)
- `/HR/Policies/` - HR policies

**Key Files:**
1. `Deployment_Runbook_v2.3.pdf` - PDF with multimodal content (text + diagrams)
2. `Payment_System_Architecture.png` - Architecture diagram (Gemini Vision)
3. `K8s_Cluster_Overview.png` - Infrastructure diagram (Gemini Vision)
4. `Q4_Financial_Strategy.pdf` - Confidential (triggers approval)
5. `Contractor_Access_Policy.pdf` - Third-party restricted

### Expertise Profiles
Automatically built from all contributions:

| Rank | Name | Score | Expertise |
|------|------|-------|-----------|
| 1 | Sarah Chen | 98.0 | deployment, architecture, mentoring |
| 2 | Diego Fernández | 87.0 | kubernetes, infrastructure, database |
| 3 | Rajesh Patel | 73.0 | security, auditing, compliance |
| 4 | Maria Gonzalez | 62.0 | authentication, security, frontend |
| 5 | Priya Sharma | 45.0 | python, learning, backend |

**Evidence Tracked:**
- Slack answers with ratings
- Documents authored
- Code reviews completed
- Incidents resolved
- Questions asked (learning indicator)

### Knowledge Gaps
Automatically detected from search patterns:

#### Gap 1: Database Migration Rollback (HIGH PRIORITY)
- 18 searches in 14 days
- 4 unique users asking
- Average result quality: 0.31 (poor)
- Suggested action: Create comprehensive runbook
- Suggested owner: Diego Fernández (database expertise: 73)
- Status: Detected
- **Demonstrates Sarah's burnout scenario**

#### Gap 2: Kubernetes Resource Limits (MEDIUM PRIORITY)
- 12 searches in 9 days
- 3 unique users
- Average result quality: 0.45
- Suggested action: Expand K8s deployment guide
- Suggested owner: Diego Fernández

## Usage

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Set environment variables (optional)
export QDRANT_URL=http://localhost:6333
export GOOGLE_API_KEY=your_gemini_key  # Optional, uses mock if not set

# Generate demo data
python backend/scripts/generate_demo_data.py
```

## Output

```
======================================================================
EngineIQ Demo Data Generator
Generating character-driven data for all 5 demo scenarios
======================================================================

📱 Generating Slack data...
   ✓ Generated 50 messages across 4 channels

🔧 Generating GitHub data...
   ✓ Generated 20 files, 3 commits

📁 Generating Box data...
   ✓ Generated 15 files across 4 folders

🔍 Indexing data to Qdrant...
   ✓ Indexed 40 items to knowledge_base collection

👨‍💻 Building expertise profiles...

📊 Detecting knowledge gaps...

======================================================================
✓ Demo Data Generation Complete!
======================================================================

📊 DEMO DATA SUMMARY
======================================================================

1. DATA GENERATED:
   • Slack Messages: 50
   • Slack Channels: 4
   • GitHub Files: 20
   • GitHub Commits: 3
   • Box Files: 15
   • Box Folders: 4

2. CHARACTERS:
   • Priya Sharma: Junior Engineer (Bangalore, India)
   • Sarah Chen: Senior Engineer / Manager (San Francisco, USA)
   • Diego Fernández: Staff Engineer (K8s Expert) (Buenos Aires, Argentina)
   • Maria Gonzalez: Engineer (Mendoza, Argentina)
   • Rajesh Patel: Security Contractor (Mumbai, India)

3. EXPERTISE SCORES:
   1. Sarah Chen: 98.0
      Topics: deployment, architecture, mentoring, devops
   2. Diego Fernández: 87.0
      Topics: kubernetes, infrastructure, database, monitoring
   3. Rajesh Patel: 73.0
      Topics: security, auditing, compliance
   4. Maria Gonzalez: 62.0
      Topics: authentication, security, frontend
   5. Priya Sharma: 45.0
      Topics: python, learning, backend

4. KNOWLEDGE GAPS DETECTED:
   1. Database migration rollback procedures
      • 18 searches by 4 users
      • Avg result quality: 0.31
      • Priority: high
      • Suggested owner: Diego Fernández (database expertise: 73)

   2. Kubernetes resource limits and requests
      • 12 searches by 3 users
      • Avg result quality: 0.45
      • Priority: medium
      • Suggested owner: Diego Fernández

5. DEMO SCENARIOS COVERED:
   ✅ Scenario 1: Priya's 2am production deployment (timezone barrier)
   ✅ Scenario 2: Rajesh contractor access (human-in-loop)
   ✅ Scenario 3: Maria & Diego Spanish/English (language barrier)
   ✅ Scenario 4: Database rollback gap (burnout prevention)
   ✅ Scenario 5: Confidential payments channel (security)

6. QDRANT COLLECTIONS:
   • knowledge_base: 40 points
   • conversations: 0 points
   • expertise_map: 5 points
   • knowledge_gaps: 2 points

7. HUMAN-IN-LOOP TRIGGERS:
   • 3 confidential files (trigger approval)
   • 1 restricted channel (#confidential-payments)

======================================================================
✅ Demo data ready for EngineIQ presentation!
======================================================================
```

## Demo Queries

After generating data, try these queries to showcase EngineIQ:

### Query 1: Priya's Production Deployment
```
"How do I deploy hotfixes to production safely?"
```
**Expected Results:**
- Sarah's Slack answer with detailed steps
- deployment.sh script from GitHub
- Deployment Runbook PDF from Box
- Shows: Breaking timezone barriers

### Query 2: Kubernetes Expert
```
"Who is the Kubernetes expert?"
```
**Expected Results:**
- Diego Fernández ranked #1 (score: 87.0)
- Evidence: 15 guides, 42 incidents resolved
- Shows: Empowering invisible talent

### Query 3: Database Migration Rollback
```
"How do we rollback database migrations?"
```
**Expected Results:**
- Low-quality scattered results
- Knowledge gap detected in dashboard
- Suggests Diego write comprehensive guide
- Shows: Proactive burnout prevention

### Query 4: Confidential Financial Data
```
"Show me Q4 financial strategy"
```
**Expected Results:**
- Human-in-loop approval modal appears
- Requires business justification
- Shows: Ethical AI with appropriate gatekeeping

### Query 5: Spanish Language
```
"¿Cómo funciona la autenticación?" (How does authentication work?)
```
**Expected Results:**
- Maria's authentication work
- English results with context
- Shows: Breaking language barriers

## Key Features Demonstrated

✅ **Timezone Barriers** - Priya gets help at 2am when SF is asleep  
✅ **Language Barriers** - Spanish queries work seamlessly  
✅ **Permission Control** - Confidential content triggers approval  
✅ **Expertise Discovery** - Diego's invisible talent becomes visible  
✅ **Knowledge Gaps** - Proactive detection prevents burnout  
✅ **Multimodal** - PDFs and diagrams analyzed by Gemini  
✅ **Human-in-Loop** - Ethical AI with appropriate gatekeeping  

## Files Created

- `backend/scripts/generate_demo_data.py` - Main generator (550+ lines)
- Characters fully defined with realistic profiles
- Coherent storylines across all 5 scenarios
- Ready for live demo presentation

---

**The demo data generator brings the DEMO_SCRIPT.md story to life with realistic, character-driven content!** 🚀
