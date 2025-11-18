#!/usr/bin/env python3
"""
EngineIQ Demo Data Generator

Generates character-driven realistic data for all 5 demo scenarios
following the story from docs/DEMO_SCRIPT.md.

Characters:
- Priya Sharma (junior engineer, Bangalore, offshore)
- Sarah Chen (senior engineer, SF, mentor)
- Diego Fernández (K8s expert, Buenos Aires)
- Maria Gonzalez (remote engineer, Argentina)
- Rajesh Patel (contractor, security expert)

Usage:
    python backend/scripts/generate_demo_data.py
"""

import sys
import os
import asyncio
import time
import uuid
import hashlib
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.services.qdrant_service import QdrantService

# Try to import GeminiService (optional)
try:
    from backend.services.gemini_service import GeminiService
except ImportError:
    GeminiService = None

# Try to import connectors (optional for demo)
try:
    from backend.connectors.slack_connector import SlackConnector
except ImportError:
    SlackConnector = None

try:
    from backend.connectors.box_connector import BoxConnector
except ImportError:
    BoxConnector = None
start_time = time.time()



# Character profiles
CHARACTERS = {
    "priya": {
        "id": "U001PRIYA",
        "name": "Priya Sharma",
        "email": "priya.sharma@engineiq.com",
        "role": "Junior Engineer",
        "location": "Bangalore, India",
        "timezone": "IST (UTC+5:30)",
        "offshore": True,
        "third_party": False,
        "teams": ["engineering"],
        "expertise": ["python", "learning", "backend"],
        "experience_months": 6,
    },
    "sarah": {
        "id": "U002SARAH",
        "name": "Sarah Chen",
        "email": "sarah.chen@engineiq.com",
        "role": "Senior Engineer / Manager",
        "location": "San Francisco, USA",
        "timezone": "PST (UTC-8)",
        "offshore": False,
        "third_party": False,
        "teams": ["engineering", "leadership"],
        "expertise": ["deployment", "architecture", "mentoring", "devops"],
        "experience_months": 96,
    },
    "diego": {
        "id": "U003DIEGO",
        "name": "Diego Fernández",
        "email": "diego.fernandez@engineiq.com",
        "role": "Staff Engineer (K8s Expert)",
        "location": "Buenos Aires, Argentina",
        "timezone": "ART (UTC-3)",
        "offshore": False,
        "third_party": False,
        "teams": ["engineering", "devops"],
        "expertise": ["kubernetes", "infrastructure", "database", "monitoring"],
        "experience_months": 84,
    },
    "maria": {
        "id": "U004MARIA",
        "name": "Maria Gonzalez",
        "email": "maria.gonzalez@engineiq.com",
        "role": "Engineer",
        "location": "Mendoza, Argentina",
        "timezone": "ART (UTC-3)",
        "offshore": False,
        "third_party": False,
        "teams": ["engineering"],
        "expertise": ["authentication", "security", "frontend"],
        "experience_months": 36,
    },
    "rajesh": {
        "id": "U005RAJESH",
        "name": "Rajesh Patel",
        "email": "rajesh.patel@contractor.com",
        "role": "Security Contractor",
        "location": "Mumbai, India",
        "timezone": "IST (UTC+5:30)",
        "offshore": True,
        "third_party": True,
        "teams": ["security-audit"],
        "expertise": ["security", "auditing", "compliance"],
        "experience_months": 120,
    },
}


class DemoDataGenerator:
    """Generate all demo data for EngineIQ"""

    def __init__(self, qdrant_service: QdrantService, gemini_service: GeminiService):
        self.qdrant = qdrant_service
        self.gemini = gemini_service
        self.base_timestamp = int(time.time()) - (30 * 86400)  # 30 days ago

    async def generate_all(self):
        """Generate all demo data"""
        print("=" * 70)
        print("EngineIQ Demo Data Generator")
        print("Generating character-driven data for all 5 demo scenarios")
        print("=" * 70)

        # Step 1: Generate Slack data
        print("\n📱 Generating Slack data...")
        slack_data = await self.generate_slack_data()
        print(f"   ✓ Generated {len(slack_data['messages'])} messages across {len(slack_data['channels'])} channels")

        # Step 2: Generate GitHub data
        print("\n🔧 Generating GitHub data...")
        github_data = await self.generate_github_data()
        print(f"   ✓ Generated {len(github_data['files'])} files, {len(github_data['commits'])} commits")

        # Step 3: Generate Box data
        print("\n📁 Generating Box data...")
        box_data = await self.generate_box_data()
        print(f"   ✓ Generated {len(box_data['files'])} files across {len(box_data['folders'])} folders")

        # Step 4: Index all data to Qdrant
        print("\n🔍 Indexing data to Qdrant...")
        await self.index_all_data(slack_data, github_data, box_data)

        # Step 5: Build expertise profiles
        print("\n👨‍💻 Building expertise profiles...")
        expertise_scores = await self.build_expertise_profiles()

        # Step 6: Create knowledge gaps
        print("\n📊 Detecting knowledge gaps...")
        knowledge_gaps = await self.create_knowledge_gaps()

        # Step 7: Print summary
        print("\n" + "=" * 70)
        print("✓ Demo Data Generation Complete!")
        print("=" * 70)

        self.print_summary(slack_data, github_data, box_data, expertise_scores, knowledge_gaps)

    async def generate_slack_data(self):
        """Generate 50 Slack messages across 5 scenarios"""
        from backend.connectors.slack_demo_data import SlackDemoDataGenerator
        
        generator = SlackDemoDataGenerator()
        
        # Use existing messages
        messages = generator.generate_all_messages()
        
        # Add more scenario-specific messages
        additional_messages = []
        
        # Scenario 1: Priya's 2am production deployment question
        ts_priya_2am = str(self.base_timestamp + 5000)
        additional_messages.extend([
            {
                "type": "message",
                "user": CHARACTERS["priya"]["id"],
                "text": """Hi team!

I have a production bug that is affecting customers right now. I need to deploy a hotfix but I have never done a production deployment solo before.

How do I deploy hotfixes to production safely? What is the process?

It is 2am here in Bangalore and everyone in SF is asleep. Really need help!""",
                "ts": ts_priya_2am,
                "thread_ts": ts_priya_2am,
                "reply_count": 2,
                "reactions": [{"name": "eyes", "count": 4}],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            {
                "type": "message",
                "user": CHARACTERS["sarah"]["id"],
                "text": """Good morning Priya! Great question - I'm glad you are being careful with prod deployments.

Here's our standard hotfix deployment process:

**Pre-deployment checklist:**
1. Create hotfix branch from main: `git checkout -b hotfix/critical-bug-fix`
2. Make your fix and add tests
3. Get code review (you can merge after 1 approval for hotfixes)
4. Run full test suite: `pytest tests/ --cov=src`

**Deployment steps:**
```bash
# 1. Tag the hotfix release
git tag -a v1.2.3-hotfix -m "Hotfix: Fix payment processing bug"
git push origin v1.2.3-hotfix

# 2. Deploy to staging first
./scripts/deploy.sh staging v1.2.3-hotfix

# 3. Run smoke tests
curl https://staging-api.engineiq.com/health
pytest tests/smoke/ -v

# 4. Deploy to production
./scripts/deploy.sh production v1.2.3-hotfix

# 5. Monitor logs
kubectl logs -f deployment/api-service -n production
```

**Post-deployment:**
- Watch Grafana for 15 minutes
- Check error rates: https://grafana.engineiq.com/d/api-errors
- Verify the fix resolved the issue
- Update the incident doc

**Rollback if needed:**
```bash
kubectl rollout undo deployment/api-service -n production
```

You've got this! Let me know if you hit any issues. I will be checking Slack periodically.""",
                "ts": str(float(ts_priya_2am) + 900),  # 15 minutes later
                "thread_ts": ts_priya_2am,
                "reactions": [
                    {"name": "+1", "count": 8},
                    {"name": "heart", "count": 3},
                    {"name": "fire", "count": 2},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            {
                "type": "message",
                "user": CHARACTERS["priya"]["id"],
                "text": """SUCCESS! Hotfix deployed and verified!

Thank you SO much @sarah.chen - your instructions were perfect. This was my first solo production deployment and it went smoothly.

The bug is fixed and customers are happy. Monitoring looks good in Grafana.

I feel like a real engineer now!""",
                "ts": str(float(ts_priya_2am) + 2400),  # 40 minutes later
                "thread_ts": ts_priya_2am,
                "reactions": [
                    {"name": "tada", "count": 12},
                    {"name": "rocket", "count": 5},
                    {"name": "clap", "count": 6},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
        ])

        # Scenario 2: Database migration rollback (creates knowledge gap)
        ts_db_1 = str(self.base_timestamp + 10000)
        for i in range(6):  # Generate 6 similar questions to trigger gap detection
            user_id = [CHARACTERS["priya"]["id"], CHARACTERS["maria"]["id"], "U006NEWENG"][i % 3]
            additional_messages.append({
                "type": "message",
                "user": user_id,
                "text": f"Quick question - how do we rollback database migrations if something goes wrong? Need this for {['production', 'staging', 'development'][i % 3]}.",
                "ts": str(self.base_timestamp + 10000 + (i * 3600 * 12)),  # Every 12 hours
                "reactions": [{"name": "eyes", "count": 2}],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            })

        # Scenario 3: Maria and Diego - Spanish to English
        ts_maria = str(self.base_timestamp + 15000)
        additional_messages.extend([
            {
                "type": "message",
                "user": CHARACTERS["maria"]["id"],
                "text": """Alguien puede ayudarme con un problema de autenticacion? 

Los usuarios no pueden iniciar sesion despues de nuestro ultimo deploy. El error es "invalid_token" pero el token se ve valido en los logs.

Anyone available to help?""",
                "ts": ts_maria,
                "thread_ts": ts_maria,
                "reply_count": 1,
                "reactions": [{"name": "eyes", "count": 3}],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            {
                "type": "message",
                "user": CHARACTERS["diego"]["id"],
                "text": """Hola Maria! Puedo ayudarte.

I see this error - looks like the JWT secret rotation didn't complete. Here's the fix:

```bash
# 1. Check current secret version
kubectl get secret api-jwt-secret -n production -o yaml

# 2. The secret should have both old and new keys during rotation
# Verify both JWT_SECRET_OLD and JWT_SECRET_NEW exist

# 3. If JWT_SECRET_NEW is missing, revert to single key:
kubectl create secret generic api-jwt-secret \\
  --from-literal=JWT_SECRET=$OLD_SECRET \\
  --namespace=production --dry-run=client -o yaml | kubectl apply -f -

# 4. Restart pods to pick up the secret
kubectl rollout restart deployment/api-service -n production
```

This should fix the authentication. Let me know if you need help!""",
                "ts": str(float(ts_maria) + 300),
                "thread_ts": ts_maria,
                "reactions": [{"name": "+1", "count": 5}, {"name": "pray", "count": 2}],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
        ])

        # Scenario 4: Rajesh security audit
        ts_rajesh = str(self.base_timestamp + 20000)
        additional_messages.extend([
            {
                "type": "message",
                "user": CHARACTERS["rajesh"]["id"],
                "text": """Security Audit Update:

I'm reviewing our Kubernetes cluster security. Need access to:
1. Current RBAC policies
2. Network policies
3. Pod security policies

These are in the k8s-configs repo, right? I have read access but want to make sure I'm looking at the right files.

Also, where are production API keys stored? Need to verify rotation policies.""",
                "ts": ts_rajesh,
                "reactions": [{"name": "lock", "count": 2}],
                "channel_id": "C003SEC",
                "channel_name": "security",
            },
            {
                "type": "message",
                "user": CHARACTERS["sarah"]["id"],
                "text": """Hi Rajesh! 

✅ **RBAC/Network policies:** Yes, all in `k8s-configs` repo under `/security/policies/`. You have read access.

✅ **API keys:** Stored in AWS Secrets Manager. I'll grant you read access to the security audit IAM role. You'll be able to list keys and see rotation dates, but not the actual secret values.

For production credentials access, I'll need written approval from your contract manager. Can you have them email me?

I've added documentation here: https://docs.engineiq.com/security/audit-procedures""",
                "ts": str(float(ts_rajesh) + 600),
                "reactions": [{"name": "+1", "count": 3}],
                "channel_id": "C003SEC",
                "channel_name": "security",
            },
        ])

        # Scenario 5: Confidential payment discussion (triggers human-in-loop)
        ts_conf = str(self.base_timestamp + 25000)
        additional_messages.extend([
            {
                "type": "message",
                "user": CHARACTERS["sarah"]["id"],
                "text": """Payment System Architecture Update - CONFIDENTIAL

We're migrating to a new payment processor next quarter. Here are the details:

**New Provider:** Stripe (replacing current provider)
**Timeline:** Q1 2025
**Budget:** $1.2M implementation cost

**Security Requirements:**
- PCI DSS Level 1 compliance
- End-to-end encryption
- Tokenization for all card data
- SOC 2 Type II certification

**API Integration:**
- REST API with OAuth 2.0
- Webhook callbacks for async events
- Rate limit: 1000 req/min
- Sandbox environment for testing

Credentials and access details are in 1Password under "Payment Migration Q1 2025".

**DO NOT share outside this channel.** This is confidential until official announcement.""",
                "ts": ts_conf,
                "reactions": [{"name": "lock", "count": 5}],
                "channel_id": "C002CONF",
                "channel_name": "confidential-payments",
            },
            {
                "type": "message",
                "user": CHARACTERS["diego"]["id"],
                "text": """I'll set up monitoring and alerts for the new payment system:

```yaml
# Prometheus alert rules
groups:
  - name: payment_system
    rules:
      - alert: HighPaymentFailureRate
        expr: rate(payment_failures_total[5m]) > 0.05
        severity: critical
        
      - alert: PaymentProcessingLatency
        expr: payment_duration_seconds > 10
        severity: warning
        
      - alert: WebhookDeliveryFailure
        expr: rate(webhook_delivery_failures[5m]) > 0.1
        severity: warning
```

Dashboard will be at: https://grafana.engineiq.com/d/payments

Also setting up PagerDuty integration for critical alerts.""",
                "ts": str(float(ts_conf) + 1800),
                "reactions": [{"name": "+1", "count": 4}],
                "channel_id": "C002CONF",
                "channel_name": "confidential-payments",
            },
        ])

        channels = generator.get_mock_channels() + [
            {
                "id": "C003SEC",
                "name": "security",
                "is_private": False,
                "context_team_id": "T001",
            }
        ]

        all_messages = messages + additional_messages

        return {
            "messages": all_messages,
            "channels": channels,
            "characters": CHARACTERS,
        }

    async def generate_github_data(self):
        """Generate GitHub repositories, files, commits, and PRs"""
        # This would integrate with GitHubConnector
        # For now, return structured data
        
        files = [
            {
                "repo": "backend-api",
                "path": "scripts/deploy.sh",
                "content": """#!/bin/bash
# Production deployment script
# Author: Sarah Chen

set -e

ENVIRONMENT=$1
VERSION=$2

if [ -z "$ENVIRONMENT" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <environment> <version>"
    exit 1
fi

echo "Deploying $VERSION to $ENVIRONMENT..."

# Run pre-deployment checks
echo "Running pre-deployment checks..."
./scripts/pre_deploy_checks.sh

# Deploy to Kubernetes
kubectl set image deployment/api-service \\
    api=engineiq/api:$VERSION \\
    -n $ENVIRONMENT

# Wait for rollout
kubectl rollout status deployment/api-service -n $ENVIRONMENT

echo "✓ Deployment complete!"
""",
                "author": "sarah.chen@engineiq.com",
                "created_at": self.base_timestamp + 1000,
            },
            {
                "repo": "k8s-configs",
                "path": "production/api-deployment.yaml",
                "content": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: production
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
    spec:
      containers:
      - name: api
        image: engineiq/api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
""",
                "author": "diego.fernandez@engineiq.com",
                "created_at": self.base_timestamp + 2000,
            },
            {
                "repo": "backend-api",
                "path": "docs/DEPLOYMENT.md",
                "content": """# Deployment Guide

## Production Deployment Process

### Prerequisites
- Code review approved
- All tests passing
- Staging deployment successful

### Steps

1. **Create Release Tag**
```bash
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

2. **Deploy to Production**
```bash
./scripts/deploy.sh production v1.2.3
```

3. **Monitor Deployment**
- Check Grafana dashboard
- Monitor error rates
- Verify health endpoints

### Rollback

If issues occur:
```bash
kubectl rollout undo deployment/api-service -n production
```

### Troubleshooting

See TROUBLESHOOTING.md for common issues and solutions.
""",
                "author": "sarah.chen@engineiq.com",
                "created_at": self.base_timestamp + 3000,
            },
        ]

        commits = [
            {
                "repo": "backend-api",
                "sha": "abc123",
                "message": "Add deployment health checks",
                "author": "Sarah Chen",
                "date": self.base_timestamp + 5000,
            },
            {
                "repo": "k8s-configs",
                "sha": "def456",
                "message": "Update resource limits for production pods",
                "author": "Diego Fernández",
                "date": self.base_timestamp + 6000,
            },
            {
                "repo": "backend-api",
                "sha": "ghi789",
                "message": "Fix payment processing bug (hotfix)",
                "author": "Priya Sharma",
                "date": self.base_timestamp + 7000,
            },
        ]

        return {"files": files, "commits": commits, "repos": ["backend-api", "k8s-configs", "deployment-scripts"]}

    async def generate_box_data(self):
        """Generate 15 Box files across folders"""
        from backend.connectors.box_demo_data import BoxDemoDataGenerator
        
        generator = BoxDemoDataGenerator()
        files = generator.generate_all_files()
        folders = generator.get_mock_folders()

        # Add a few more scenario-specific files
        additional_files = [
            {
                "id": "file_008",
                "name": "Contractor_Access_Policy.pdf",
                "type": "file",
                "size": 156000,
                "created_at": self.base_timestamp + 40000,
                "modified_at": self.base_timestamp + 40000,
                "folder": folders[2],  # HR/Policies
                "content_type": "pdf",
                "file_type": "pdf",
                "owner": "hr@engineiq.com",
                "shared_users": [],
                "is_public": False,
                "tags": ["policy", "contractor", "third-party", "security"],
                "comments": [],
                "raw_content": """CONTRACTOR ACCESS POLICY

Scope: This policy applies to all third-party contractors.

Access Principles:
1. Least privilege access
2. Time-bound access (contract duration only)
3. Audit trail for all actions
4. No access to financial or personal data without approval

Technical Documentation Access:
YES Contractors have automatic read access to:
- Public technical documentation
- Non-confidential architecture diagrams
- Development guides and runbooks

Restricted Access (Requires Approval):
NO Contractors need written approval for:
- Production credentials and API keys
- Financial projections and budgets
- Employee personal information
- Customer data
- Source code repositories (case-by-case)

Approval Process:
1. Contractor submits request with business justification
2. Hiring manager reviews and approves
3. Security team grants time-bound access
4. Access automatically revoked at contract end

Compliance:
All contractor access is logged and audited quarterly.
""",
                "mock_gemini_result": None,
            },
        ]

        return {
            "files": files + additional_files,
            "folders": folders,
        }

    async def index_all_data(self, slack_data, github_data, box_data):
        """Index all generated data to Qdrant"""
        # Initialize collections
        self.qdrant.initialize_collections()

        total_indexed = 0

        # Index Slack messages
        for message in slack_data["messages"][:20]:  # Index subset for demo
            try:
                # Create mock SlackConnector behavior
                channel = next(c for c in slack_data["channels"] if c["id"] == message["channel_id"])
                
                # Generate UUID from consistent string
                item_id_str = f"slack_{message['channel_id']}_{message['ts']}"
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item_id_str))
                
                item = {
                    "id": item_id,
                    "title": f"#{message['channel_name']} - {message.get('text', '')[:50]}...",
                    "raw_content": message["text"],
                    "content_type": "code" if "```" in message["text"] else "text",
                    "file_type": "md",
                    "url": f"https://engineiq.slack.com/archives/{message['channel_id']}/p{message['ts'].replace('.', '')}",
                    "created_at": int(float(message["ts"])),
                    "modified_at": int(float(message["ts"])),
                    "owner": message["user"],
                    "contributors": [message["user"]],
                    "permissions": {
                        "public": not channel.get("is_private", False),
                        "teams": ["engineering"],
                        "users": [],
                        "sensitivity": "confidential" if "confidential" in channel["name"] else "internal",
                        "offshore_restricted": False,
                        "third_party_restricted": channel.get("is_private", False),
                    },
                    "metadata": {
                        "slack_channel": message["channel_name"],
                        "slack_reactions": [r["name"] for r in message.get("reactions", [])],
                    },
                }

                # Generate embedding (real if gemini available, mock otherwise)
                if self.gemini:
                    try:
                        embedding = self.gemini.generate_embedding(message["text"])
                    except Exception as e:
                        print(f"   Warning: Failed to generate embedding, using mock: {e}")
                        embedding = [0.1] * 768
                else:
                    embedding = [0.1] * 768

                self.qdrant.index_document(
                    collection_name="knowledge_base",
                    doc_id=item["id"],
                    vector=embedding,
                    payload=item,
                )
                total_indexed += 1

            except Exception as e:
                print(f"   Error indexing message: {e}")

        # Index GitHub files
        for file in github_data["files"][:10]:  # Index subset
            try:
                # Generate UUID from consistent string
                item_id_str = f"github_{file['repo']}_{file['path'].replace('/', '_')}"
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item_id_str))
                
                item = {
                    "id": item_id,
                    "title": f"{file['repo']}/{file['path']}",
                    "raw_content": file["content"],
                    "content_type": "code" if file["path"].endswith(".sh") or file["path"].endswith(".yaml") else "text",
                    "file_type": file["path"].split(".")[-1],
                    "url": f"https://github.com/engineiq/{file['repo']}/blob/main/{file['path']}",
                    "created_at": file["created_at"],
                    "modified_at": file["created_at"],
                    "owner": file["author"],
                    "contributors": [file["author"]],
                    "permissions": {
                        "public": False,
                        "teams": ["engineering"],
                        "users": [],
                        "sensitivity": "internal",
                        "offshore_restricted": False,
                        "third_party_restricted": True,
                    },
                    "metadata": {"github_repo": file["repo"], "github_path": file["path"]},
                }

                # Generate embedding
                if self.gemini:
                    try:
                        embedding = self.gemini.generate_embedding(file["content"])
                    except:
                        embedding = [0.1] * 768
                else:
                    embedding = [0.1] * 768
                    
                self.qdrant.index_document(
                    collection_name="knowledge_base",
                    doc_id=item["id"],
                    vector=embedding,
                    payload=item,
                )
                total_indexed += 1

            except Exception as e:
                print(f"   Error indexing GitHub file: {e}")

        # Index Box files
        for file in box_data["files"][:10]:  # Index subset
            try:
                # Generate UUID from consistent string
                item_id_str = f"box_{file['id']}"
                item_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, item_id_str))
                
                item = {
                    "id": item_id,
                    "title": file["name"],
                    "raw_content": file["raw_content"] if isinstance(file["raw_content"], str) else "",
                    "content_type": file["content_type"],
                    "file_type": file["file_type"],
                    "url": f"https://app.box.com/file/{file['id']}",
                    "created_at": file["created_at"],
                    "modified_at": file["modified_at"],
                    "owner": file["owner"],
                    "contributors": file["shared_users"],
                    "permissions": {
                        "public": file["is_public"],
                        "teams": ["engineering"] if not file["is_public"] else [],
                        "users": file["shared_users"],
                        "sensitivity": "confidential" if "confidential" in file["name"].lower() else "internal",
                        "offshore_restricted": "confidential" in file["name"].lower(),
                        "third_party_restricted": "restricted" in file["name"].lower() or "confidential" in file["name"].lower(),
                    },
                    "metadata": {
                        "box_folder_path": file["folder"]["path"],
                        "box_tags": file["tags"],
                    },
                }

                # Generate embedding
                content_for_embedding = file.get("raw_content", "") if isinstance(file.get("raw_content"), str) else file.get("name", "")
                if self.gemini:
                    try:
                        embedding = self.gemini.generate_embedding(content_for_embedding[:5000])
                    except:
                        embedding = [0.1] * 768
                else:
                    embedding = [0.1] * 768
                    
                self.qdrant.index_document(
                    collection_name="knowledge_base",
                    doc_id=item["id"],
                    vector=embedding,
                    payload=item,
                )
                total_indexed += 1

            except Exception as e:
                print(f"   Error indexing Box file: {e}")

        print(f"   ✓ Indexed {total_indexed} items to knowledge_base collection")

    async def build_expertise_profiles(self):
        """Build expertise profiles for all characters"""
        profiles = {}

        # Sarah Chen - Senior with highest expertise
        sarah_score = 98.0
        sarah_evidence = [
            {"action": "authored", "doc": "Deployment Runbook", "score": 3.0},
            {"action": "answered", "doc": "50+ Slack questions", "score": 75.0},
            {"action": "reviewed", "doc": "100+ code reviews", "score": 20.0},
        ]
        profiles["sarah"] = {"score": sarah_score, "evidence": sarah_evidence, "rank": 1}

        # Diego Fernández - K8s expert
        diego_score = 87.0
        diego_evidence = [
            {"action": "authored", "doc": "15 K8s guides", "score": 45.0},
            {"action": "resolved", "doc": "42 production incidents", "score": 42.0},
        ]
        profiles["diego"] = {"score": diego_score, "evidence": diego_evidence, "rank": 2}

        # Priya Sharma - Junior, growing expertise
        priya_score = 45.0
        priya_evidence = [
            {"action": "asked", "doc": "Learning questions", "score": 10.0},
            {"action": "authored", "doc": "Hotfix deployment", "score": 35.0},
        ]
        profiles["priya"] = {"score": priya_score, "evidence": priya_evidence, "rank": 3}

        # Maria Gonzalez - Auth expert
        maria_score = 62.0
        maria_evidence = [
            {"action": "authored", "doc": "Authentication features", "score": 52.0},
            {"action": "answered", "doc": "Auth questions", "score": 10.0},
        ]
        profiles["maria"] = {"score": maria_score, "evidence": maria_evidence, "rank": 4}

        # Rajesh Patel - Security expert
        rajesh_score = 73.0
        rajesh_evidence = [
            {"action": "audited", "doc": "Security reviews", "score": 63.0},
            {"action": "documented", "doc": "Security policies", "score": 10.0},
        ]
        profiles["rajesh"] = {"score": rajesh_score, "evidence": rajesh_evidence, "rank": 5}

        # Index to expertise_map collection
        for char_id, profile in profiles.items():
            char = CHARACTERS[char_id]
            
            # Generate embedding from expertise description
            expertise_text = f"{char['name']} expertise: {', '.join(char.get('expertise_areas', []))}"
            if self.gemini:
                try:
                    embedding = self.gemini.generate_embedding(expertise_text)
                except:
                    embedding = [0.1] * 768
            else:
                embedding = [0.1] * 768

            # Generate UUID from consistent string
            expert_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"expert_{char_id}"))
            
            self.qdrant.index_document(
                collection_name="expertise_map",
                doc_id=expert_id,
                vector=embedding,
                payload={
                    "user_id": char["id"],
                    "user_name": char["name"],
                    "topic": ", ".join(char["expertise"]),
                    "expertise_score": profile["score"],
                    "evidence": profile["evidence"],
                    "last_contribution": self.base_timestamp + 10000,
                    "contribution_count": len(profile["evidence"]),
                    "tags": char["expertise"],
                    "trend": "increasing" if char_id == "priya" else "stable",
                },
            )

        return profiles

    async def create_knowledge_gaps(self):
        """Create knowledge gaps for demo"""
        gaps = []

        # Knowledge Gap: Database migration rollback (18+ searches)
        gap1 = {
            "id": "gap_db_rollback",
            "topic": "Database migration rollback procedures",
            "query_patterns": [
                "How do we rollback database migrations?",
                "Database rollback procedure",
                "Undo migration in production",
            ],
            "query_count": 18,
            "unique_users": ["U001PRIYA", "U004MARIA", "U006NEWENG", "U007INTERN"],
            "avg_result_quality": 0.31,
            "first_detected": self.base_timestamp + 10000,
            "last_query": self.base_timestamp + 25000,
            "priority": "high",
            "suggested_action": "Create comprehensive runbook: 'Database Migration Rollback Procedures'",
            "suggested_owner": "Diego Fernández (database expertise: 73)",
            "status": "detected",
            "related_docs": [],
        }
        gaps.append(gap1)

        # Knowledge Gap: Kubernetes resource limits
        gap2 = {
            "id": "gap_k8s_resources",
            "topic": "Kubernetes resource limits and requests",
            "query_patterns": [
                "K8s resource limits best practices",
                "How to set memory limits",
                "Pod resource configuration",
            ],
            "query_count": 12,
            "unique_users": ["U001PRIYA", "U004MARIA", "U006NEWENG"],
            "avg_result_quality": 0.45,
            "first_detected": self.base_timestamp + 15000,
            "last_query": self.base_timestamp + 24000,
            "priority": "medium",
            "suggested_action": "Expand K8s deployment guide with resource configuration section",
            "suggested_owner": "Diego Fernández",
            "status": "detected",
            "related_docs": ["k8s-configs/production/api-deployment.yaml"],
        }
        gaps.append(gap2)

        # Index to knowledge_gaps collection
        for gap in gaps:
            # Generate embedding from gap description
            gap_text = f"{gap['topic']}: {gap.get('description', '')}"
            if self.gemini:
                try:
                    embedding = self.gemini.generate_embedding(gap_text)
                except:
                    embedding = [0.1] * 768
            else:
                embedding = [0.1] * 768
                
            # Generate UUID from gap ID
            gap_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, gap["id"]))
            
            self.qdrant.index_document(
                collection_name="knowledge_gaps",
                doc_id=gap_id,
                vector=embedding,
                payload=gap,
            )

        return gaps

        end_time = time.time()
        print(f"\n📊 Performance Metrics:")
        print(f"  • Total indexing time: {end_time - start_time:.2f}s")
        print(f"  • Documents/second: {total_docs / (end_time - start_time):.1f}")
        print(f"  • Average embedding time: {total_embedding_time / total_docs:.3f}s")


    def print_summary(self, slack_data, github_data, box_data, expertise_scores, knowledge_gaps):
        """Print comprehensive summary"""
        print("\n📊 DEMO DATA SUMMARY")
        print("=" * 70)

        print("\n1. DATA GENERATED:")
        print(f"   • Slack Messages: {len(slack_data['messages'])}")
        print(f"   • Slack Channels: {len(slack_data['channels'])}")
        print(f"   • GitHub Files: {len(github_data['files'])}")
        print(f"   • GitHub Commits: {len(github_data['commits'])}")
        print(f"   • Box Files: {len(box_data['files'])}")
        print(f"   • Box Folders: {len(box_data['folders'])}")

        print("\n2. CHARACTERS:")
        for char_id, char in CHARACTERS.items():
            print(f"   • {char['name']}: {char['role']} ({char['location']})")

        print("\n3. EXPERTISE SCORES:")
        sorted_experts = sorted(
            expertise_scores.items(), key=lambda x: x[1]["score"], reverse=True
        )
        for char_id, profile in sorted_experts:
            char = CHARACTERS[char_id]
            print(f"   {profile['rank']}. {char['name']}: {profile['score']:.1f}")
            print(f"      Topics: {', '.join(char['expertise'])}")

        print("\n4. KNOWLEDGE GAPS DETECTED:")
        for i, gap in enumerate(knowledge_gaps, 1):
            print(f"   {i}. {gap['topic']}")
            print(f"      • {gap['query_count']} searches by {len(gap['unique_users'])} users")
            print(f"      • Avg result quality: {gap['avg_result_quality']:.2f}")
            print(f"      • Priority: {gap['priority']}")
            print(f"      • Suggested owner: {gap['suggested_owner']}")

        print("\n5. DEMO SCENARIOS COVERED:")
        print("   ✅ Scenario 1: Priya's 2am production deployment (timezone barrier)")
        print("   ✅ Scenario 2: Rajesh contractor access (human-in-loop)")
        print("   ✅ Scenario 3: Maria & Diego Spanish/English (language barrier)")
        print("   ✅ Scenario 4: Database rollback gap (burnout prevention)")
        print("   ✅ Scenario 5: Confidential payments channel (security)")

        print("\n6. QDRANT COLLECTIONS:")
        for collection in ["knowledge_base", "conversations", "expertise_map", "knowledge_gaps"]:
            stats = self.qdrant.get_collection_stats(collection)
            print(f"   • {collection}: {stats.get('points_count', 0)} points")

        print("\n7. HUMAN-IN-LOOP TRIGGERS:")
        confidential_files = [
            f for f in box_data["files"] if "confidential" in f["name"].lower()
        ]
        print(f"   • {len(confidential_files)} confidential files (trigger approval)")
        print(f"   • 1 restricted channel (#confidential-payments)")

        print("\n" + "=" * 70)
        print("✅ Demo data ready for EngineIQ presentation!")
        print("=" * 70)

        print("\n📝 NEXT STEPS:")
        print("   1. Start EngineIQ API server")
        print("   2. Query: 'How do I deploy hotfixes to production?'")
        print("   3. Show Priya's result with Sarah's answer + deployment script")
        print("   4. Query confidential content to trigger human-in-loop")
        print("   5. Show expertise ranking with Diego at top for K8s")
        print("   6. Display knowledge gap dashboard showing database rollback gap")


async def main():
    """Main execution"""
    print("\nInitializing services...")

    # Initialize Qdrant
    qdrant = QdrantService(
        url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        api_key=os.getenv("QDRANT_API_KEY"),
    )

    if not qdrant.health_check():
        print("❌ Qdrant is not available. Please start Qdrant:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        return

    # Initialize Gemini (with mock if no API key)
    # Check both GEMINI_API_KEY (correct) and GOOGLE_API_KEY (legacy)
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        try:
            from backend.services.gemini_service import GeminiService
            # GeminiService reads GEMINI_API_KEY from environment automatically
            gemini = GeminiService()
            print(f"✅ Using real Gemini embeddings (API key found)")
        except Exception as e:
            print(f"⚠️  Could not initialize GeminiService: {e}")
            print("   Using mock embeddings instead")
            gemini = None
    else:
        print("⚠️  No GEMINI_API_KEY or GOOGLE_API_KEY found, using mock embeddings")
        gemini = None

    # Generate all demo data
    generator = DemoDataGenerator(qdrant, gemini)
    await generator.generate_all()


if __name__ == "__main__":
    asyncio.run(main())
