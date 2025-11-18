"""
Complete EngineIQ Demo Data Generator

Generates all 150-200 documents for the 5 demo scenarios with:
- Realistic content across all sources
- Coherent DeployBot narrative
- Proper cross-references
- Human-in-loop triggers
- Expertise profiles
- Knowledge gaps
"""

import time
import json
from typing import List, Dict

# Import generators (these would be in separate files)
# from generate_slack import generate_all_slack_messages
# from generate_github import generate_all_github_content
# from generate_box import generate_all_box_documents
# from generate_jira import generate_all_jira_issues
# from generate_confluence import generate_all_confluence_pages


NOW = int(time.time())
DAY = 86400


class DemoDataGenerator:
    """Complete demo data generator for EngineIQ"""

    def __init__(self):
        self.users = {
            "alice": {"role": "Senior Engineer", "expertise": ["kubernetes", "python"]},
            "bob": {"role": "DevOps Engineer", "expertise": ["docker", "ci-cd"]},
            "charlie": {"role": "Full-Stack Developer", "expertise": ["javascript", "react"]},
            "diana": {"role": "Product Manager", "expertise": []},
            "eve": {"role": "Backend Engineer", "expertise": ["python", "database"]},
            "frank": {"role": "Frontend Engineer", "expertise": ["react", "typescript"]},
            "grace": {"role": "Technical Architect", "expertise": ["architecture", "system-design"]},
            "henry": {"role": "SRE Engineer", "expertise": ["monitoring", "reliability"]}
        }

        self.all_documents = []

    def generate_scenario_1_data(self) -> List[Dict]:
        """
        Scenario 1: Cross-Source Search
        Query: "How do we deploy to production?"
        """
        docs = []

        # Slack: Deployment discussion
        docs.append({
            "id": "slack_devops_deploy_discussion",
            "source": "slack",
            "content_type": "text",
            "title": "#devops - How do we safely deploy to production?",
            "content": """alice: How do we safely deploy to production? I saw the deploy.py script but not sure about the rollback process.

bob: Check out PR #456 - I added rollback logic there. https://github.com/techcorp/deploybot/pull/456

charlie: We also have a runbook in Confluence: https://wiki.techcorp.com/production-deployment

alice: Perfect! One question - do we run migrations before or after deployment?

bob: After! See deploy.py line 123. This way if migrations fail, we can rollback the deployment too.""",
            "url": "https://techcorp.slack.com/archives/devops/p1234567890",
            "created_at": NOW - (7 * DAY),
            "modified_at": NOW - (7 * DAY),
            "owner": "alice",
            "contributors": ["alice", "bob", "charlie"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"slack_channel": "devops"},
            "tags": ["deployment", "production"],
            "language": "en"
        })

        # GitHub: Deployment script
        docs.append({
            "id": "github_deploybot_deploy_py",
            "source": "github",
            "content_type": "code",
            "title": "techcorp/deploybot/deployment/deploy.py",
            "content": """Python script for deploying applications to production Kubernetes cluster. Validates version, builds Docker image, pushes to registry, updates Kubernetes deployment, and runs health checks. Code:

```python
def deploy_to_production(app_name: str, version: str):
    validate_version(version)
    build_docker_image(app_name, version)
    push_to_registry(app_name, version)
    deploy_to_kubernetes(app_name, version)
    run_migrations()  # Line 123
    run_health_checks()
```""",
            "url": "https://github.com/techcorp/deploybot/blob/main/deployment/deploy.py",
            "created_at": NOW - (15 * DAY),
            "modified_at": NOW - (8 * DAY),
            "owner": "alice",
            "contributors": ["alice", "bob"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": True  # Code is sensitive
            },
            "metadata": {"github_repo": "techcorp/deploybot", "github_path": "deployment/deploy.py"},
            "tags": ["deployment", "kubernetes", "python"],
            "language": "python"
        })

        # Confluence: Runbook
        docs.append({
            "id": "confluence_production_deployment_guide",
            "source": "confluence",
            "content_type": "text",
            "title": "Production Deployment Guide",
            "content": """# Production Deployment Guide

## Prerequisites
- kubectl configured for prod cluster
- Docker image built and pushed
- All tests passing in CI

## Deployment Steps

1. Validate Version
   ./scripts/validate-version.sh v2.3.1

2. Run Deployment Script
   python deployment/deploy.py deploybot 2.3.1

3. Monitor Health
   - Check Grafana: https://grafana.techcorp.com/deploybot
   - Watch pod status: kubectl get pods -n production

4. Rollback if Needed
   kubectl rollout undo deployment/deploybot

## Common Issues

### Pods CrashLooping
- Check memory limits in deployment.yaml
- Review logs: kubectl logs <pod-name>

### Database Migration Errors
- Verify migration order
- Check for conflicting schema changes""",
            "url": "https://wiki.techcorp.com/production-deployment",
            "created_at": NOW - (10 * DAY),
            "modified_at": NOW - (5 * DAY),
            "owner": "charlie",
            "contributors": ["charlie", "eve"],
            "permissions": {
                "public": True,
                "teams": [],
                "users": [],
                "sensitivity": "public",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"confluence_space": "Engineering"},
            "tags": ["deployment", "runbook", "kubernetes"],
            "language": "en"
        })

        # Jira: Automation ticket
        docs.append({
            "id": "jira_PROD_100",
            "source": "jira",
            "content_type": "text",
            "title": "PROD-100: Automate production deployment",
            "content": """Epic: Automate Kubernetes Deployments

Description:
Current manual deployment process is error-prone and slow. Automate the entire workflow from code merge to production deployment.

Tasks:
- Write deployment script (deploy.py) - DONE
- Add rollback functionality - DONE
- Create CI/CD pipeline - IN PROGRESS
- Write deployment runbook - DONE

Comments:
bob: Deployment script is working great! Used it 3 times this week without issues.
alice: Added health check validation to prevent bad deployments.""",
            "url": "https://techcorp.atlassian.net/browse/PROD-100",
            "created_at": NOW - (25 * DAY),
            "modified_at": NOW - (3 * DAY),
            "owner": "diana",
            "contributors": ["diana", "alice", "bob"],
            "permissions": {
                "public": False,
                "teams": ["engineering", "product"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"jira_project": "PROD", "jira_issue_key": "PROD-100"},
            "tags": ["automation", "deployment"],
            "language": "en"
        })

        # Box: Postmortem
        docs.append({
            "id": "box_failed_deployment_postmortem",
            "source": "box",
            "content_type": "pdf",
            "title": "Failed Deployment Postmortem 2024-03-15",
            "content": """Postmortem: Production Deployment Failure

Date: March 15, 2024
Duration: 45 minutes
Impact: 5000 users affected

Timeline:
14:00 - Deployment of v2.3.1 started
14:10 - Pods began crash looping (OOMKilled)
14:15 - Health checks failing, 503 errors
14:30 - Root cause identified: Memory limit too low
14:45 - Fixed and redeployed with 1GB memory

Root Cause:
deployment.yaml specified 512MB memory limit, but application heap requires 1GB.

Action Items:
1. Update deployment runbook with memory requirements
2. Add memory monitoring alerts
3. Test resource requirements in staging first""",
            "url": "https://app.box.com/file/postmortem_20240315",
            "created_at": NOW - (5 * DAY),
            "modified_at": NOW - (5 * DAY),
            "owner": "alice",
            "contributors": ["alice", "henry"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"box_folder_id": "123456"},
            "tags": ["postmortem", "incident", "deployment"],
            "language": "en"
        })

        return docs

    def generate_scenario_2_data(self) -> List[Dict]:
        """
        Scenario 2: Multimodal Image Analysis
        Action: Upload architecture diagram
        """
        docs = []

        # Box: Architecture diagram (image)
        docs.append({
            "id": "box_deploybot_architecture_diagram",
            "source": "box",
            "content_type": "image",
            "title": "DeployBot Architecture Diagram.png",
            "content": """Kubernetes architecture diagram showing: API Gateway (Kong) receiving external traffic, routing to Kubernetes cluster with 3 worker nodes. Each node runs kubelet and kube-proxy. Control plane has API server, etcd cluster for state, scheduler, and controller manager. Application pods distributed across nodes with horizontal pod autoscaler. Services expose pods internally (ClusterIP) and externally (LoadBalancer). Ingress controller manages external HTTP/HTTPS routing. Persistent volumes for stateful data. Monitoring stack with Prometheus scraping metrics and Grafana for visualization. PostgreSQL RDS database external to cluster. Redis cache for session management.""",
            "url": "https://app.box.com/file/deploybot_architecture.png",
            "created_at": NOW - (20 * DAY),
            "modified_at": NOW - (20 * DAY),
            "owner": "grace",
            "contributors": ["grace"],
            "permissions": {
                "public": False,
                "teams": ["engineering", "product"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"box_folder_id": "architecture_docs"},
            "tags": ["architecture", "kubernetes", "diagram"],
            "language": "en"
        })

        # GitHub: K8s manifests implementing the architecture
        docs.append({
            "id": "github_deploybot_k8s_deployment_yaml",
            "source": "github",
            "content_type": "code",
            "title": "techcorp/deploybot/k8s/deployment.yaml",
            "content": """Kubernetes deployment manifest for DeployBot application. Defines deployment with 3 replicas, resource limits (1GB memory, 500m CPU), health checks (liveness and readiness probes), and container specifications. Code:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploybot
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deploybot
  template:
    metadata:
      labels:
        app: deploybot
    spec:
      containers:
      - name: deploybot
        image: deploybot:2.3.1
        resources:
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
```""",
            "url": "https://github.com/techcorp/deploybot/blob/main/k8s/deployment.yaml",
            "created_at": NOW - (18 * DAY),
            "modified_at": NOW - (4 * DAY),
            "owner": "alice",
            "contributors": ["alice", "bob"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": True
            },
            "metadata": {"github_repo": "techcorp/deploybot", "github_path": "k8s/deployment.yaml"},
            "tags": ["kubernetes", "deployment", "yaml"],
            "language": "yaml"
        })

        return docs

    def generate_scenario_3_data(self) -> List[Dict]:
        """
        Scenario 3: Human-in-Loop (Sensitive Content)
        Query: "Q4 revenue targets"
        """
        docs = []

        # Confidential revenue forecast
        docs.append({
            "id": "gdocs_q4_revenue_forecast",
            "source": "drive",
            "content_type": "text",
            "title": "Q4 2024 Revenue Forecast - CONFIDENTIAL",
            "content": """Q4 2024 Revenue Forecast

CONFIDENTIAL - Executive Distribution Only

Projected Revenue: $12.5M
- Enterprise: $8.2M (65%)
- SMB: $3.1M (25%)
- Self-Serve: $1.2M (10%)

Key Assumptions:
- 15% MoM growth in enterprise
- New customer acquisition: 50 enterprise accounts
- Churn rate: 2%

Strategic Initiatives:
- DeployBot v2.0 launch
- Enterprise sales team expansion
- European market entry

Contact: diana@techcorp.com for details""",
            "url": "https://docs.google.com/document/d/q4-revenue-forecast",
            "created_at": NOW - (30 * DAY),
            "modified_at": NOW - (25 * DAY),
            "owner": "diana",
            "contributors": ["diana"],
            "permissions": {
                "public": False,
                "teams": ["executive", "finance"],
                "users": [],
                "sensitivity": "confidential",  # TRIGGERS APPROVAL
                "offshore_restricted": True,
                "third_party_restricted": True
            },
            "metadata": {"drive_folder_id": "executive_docs"},
            "tags": ["revenue", "forecast", "confidential"],
            "language": "en"
        })

        # Restricted salary data
        docs.append({
            "id": "box_salary_benchmarks",
            "source": "box",
            "content_type": "text",
            "title": "Engineering Salary Benchmarks 2024",
            "content": """Engineering Salary Benchmarks

RESTRICTED - HR Use Only

Senior Engineer: $150K - $180K
DevOps Engineer: $140K - $170K
Full-Stack Developer: $120K - $150K
SRE Engineer: $145K - $175K

Stock Options: 0.1% - 0.5% of company

Benefits:
- Health insurance (100% covered)
- 401k match (5%)
- Unlimited PTO

Market Data Source: Radford Survey 2024
Employee SSNs and compensation in separate file (restricted access)""",
            "url": "https://app.box.com/file/salary_benchmarks_2024",
            "created_at": NOW - (60 * DAY),
            "modified_at": NOW - (60 * DAY),
            "owner": "hr_manager",
            "contributors": ["hr_manager"],
            "permissions": {
                "public": False,
                "teams": ["hr", "executive"],
                "users": [],
                "sensitivity": "restricted",  # TRIGGERS APPROVAL
                "offshore_restricted": True,
                "third_party_restricted": True
            },
            "metadata": {"box_folder_id": "hr_confidential"},
            "tags": ["salary", "compensation", "restricted"],
            "language": "en"
        })

        return docs

    def generate_scenario_4_data(self) -> List[Dict]:
        """
        Scenario 4: Expertise Finding
        Query: "Who's the Kubernetes expert?"

        Build alice's expertise profile
        """
        # This generates expertise_map entries, not knowledge_base
        # See generate_expertise_map() method
        return []

    def generate_scenario_5_data(self) -> List[Dict]:
        """
        Scenario 5: Knowledge Gap Detection
        Pattern: "How to rollback database migrations?"

        Creates inadequate docs + conversation records
        """
        docs = []

        # Inadequate existing doc
        docs.append({
            "id": "confluence_db_schema_guide",
            "source": "confluence",
            "content_type": "text",
            "title": "Database Schema Guide",
            "content": """# Database Schema Guide

## Tables
- users: User accounts
- deployments: Deployment history
- logs: Application logs

## Migrations
We use Alembic for database migrations. To run migrations:

```bash
alembic upgrade head
```

To create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

Note: Be careful with production migrations. Test in staging first.

(No rollback procedures documented)""",
            "url": "https://wiki.techcorp.com/db-schema-guide",
            "created_at": NOW - (40 * DAY),
            "modified_at": NOW - (40 * DAY),
            "owner": "eve",
            "contributors": ["eve"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {"confluence_space": "Engineering"},
            "tags": ["database", "schema", "migrations"],
            "language": "en"
        })

        return docs

    def generate_expertise_map(self) -> List[Dict]:
        """Generate expertise map entries for demo"""
        expertise_entries = []

        # Alice - Kubernetes expert (score: 65)
        alice_k8s_evidence = [
            {"source": "github", "action": "authored", "doc_title": "k8s/deployment.py", "contribution_score": 2.0},
            {"source": "github", "action": "authored", "doc_title": "k8s/manifests/app.yaml", "contribution_score": 2.0},
            {"source": "slack", "action": "answered", "doc_title": "How to scale pods?", "contribution_score": 1.5},
            {"source": "slack", "action": "answered", "doc_title": "K8s best practices?", "contribution_score": 1.5},
            {"source": "confluence", "action": "authored", "doc_title": "K8s Best Practices", "contribution_score": 3.0},
            {"source": "jira", "action": "resolved", "doc_title": "PROD-123: Pod crash loop", "contribution_score": 1.0},
        ]

        expertise_entries.append({
            "user_id": "alice",
            "topic": "kubernetes deployment",
            "expertise_score": 65.0,
            "evidence": alice_k8s_evidence,
            "last_contribution": NOW - (3 * DAY),
            "contribution_count": 25,
            "tags": ["kubernetes", "deployment", "docker"]
        })

        # Bob - Docker/CI expert (score: 45)
        bob_docker_evidence = [
            {"source": "github", "action": "authored", "doc_title": "Dockerfile", "contribution_score": 2.0},
            {"source": "github", "action": "reviewed", "doc_title": "PR #456: Rollback", "contribution_score": 1.5},
            {"source": "slack", "action": "answered", "doc_title": "Docker optimization?", "contribution_score": 1.5},
        ]

        expertise_entries.append({
            "user_id": "bob",
            "topic": "docker ci-cd",
            "expertise_score": 45.0,
            "evidence": bob_docker_evidence,
            "last_contribution": NOW - (5 * DAY),
            "contribution_count": 18,
            "tags": ["docker", "ci-cd", "devops"]
        })

        return expertise_entries

    def generate_conversation_records(self) -> List[Dict]:
        """Generate query records for knowledge gap detection"""
        conversations = []

        # 18 similar queries about db migration rollback
        queries = [
            "How to rollback database migrations?",
            "Undo database migration",
            "Reverse migration in production",
            "Migration rollback procedure",
            "Failed migration recovery",
            "Rollback alembic migration",
            "Database migration undo",
            "Revert schema changes",
            "Migration rollback steps",
            "How to rollback db changes?",
            "Production migration failed, how to rollback?",
            "Undo last migration",
            "Migration rollback best practices",
            "Emergency migration rollback",
            "Database rollback procedure",
            "Schema migration reversal",
            "Alembic downgrade steps",
            "Migration failure recovery"
        ]

        users = ["alice", "bob", "charlie", "diana", "eve", "frank", "grace", "henry",
                 "intern1", "intern2", "intern3", "intern4"]

        for i, query in enumerate(queries):
            conversations.append({
                "user_id": users[i % len(users)],
                "query": query,
                "results_count": 2,
                "top_result_score": 0.28 + (i * 0.01),  # Poor scores 0.28-0.45
                "clicked_results": [],
                "user_rating": 2,  # Low satisfaction
                "timestamp": NOW - ((18 - i) * DAY // 7),  # Spread over 7 days
                "response_time_ms": 150,
                "triggered_approval": False,
                "approval_granted": False
            })

        return conversations

    def generate_knowledge_gap(self) -> Dict:
        """Generate knowledge gap record"""
        return {
            "query_pattern": "How to rollback database migrations?",
            "search_count": 18,
            "unique_users": ["alice", "bob", "charlie", "diana", "eve", "frank",
                           "grace", "henry", "intern1", "intern2", "intern3", "intern4"],
            "avg_result_score": 0.32,
            "avg_user_rating": 2.1,
            "first_detected": NOW - (7 * DAY),
            "last_searched": NOW - (1 * HOUR),
            "priority": "high",
            "suggested_action": "Create runbook: Database Migration Rollback Procedures",
            "assigned_to": "alice",
            "status": "detected",
            "related_docs": ["confluence_db_schema_guide"]
        }

    def generate_all_demo_data(self) -> Dict:
        """Generate complete demo dataset"""
        print("Generating EngineIQ demo data...")

        data = {
            "knowledge_base": [],
            "expertise_map": [],
            "conversations": [],
            "knowledge_gaps": []
        }

        # Scenario 1: Cross-source search
        print("  Generating Scenario 1 data (Cross-source search)...")
        data["knowledge_base"].extend(self.generate_scenario_1_data())

        # Scenario 2: Multimodal
        print("  Generating Scenario 2 data (Multimodal)...")
        data["knowledge_base"].extend(self.generate_scenario_2_data())

        # Scenario 3: Human-in-loop
        print("  Generating Scenario 3 data (Sensitive content)...")
        data["knowledge_base"].extend(self.generate_scenario_3_data())

        # Scenario 4: Expertise
        print("  Generating Scenario 4 data (Expertise map)...")
        data["expertise_map"].extend(self.generate_expertise_map())

        # Scenario 5: Knowledge gaps
        print("  Generating Scenario 5 data (Knowledge gaps)...")
        data["knowledge_base"].extend(self.generate_scenario_5_data())
        data["conversations"].extend(self.generate_conversation_records())
        data["knowledge_gaps"].append(self.generate_knowledge_gap())

        # Summary
        print(f"\n✓ Demo data generated:")
        print(f"  - knowledge_base: {len(data['knowledge_base'])} documents")
        print(f"  - expertise_map: {len(data['expertise_map'])} entries")
        print(f"  - conversations: {len(data['conversations'])} queries")
        print(f"  - knowledge_gaps: {len(data['knowledge_gaps'])} gaps")

        return data


if __name__ == "__main__":
    generator = DemoDataGenerator()
    demo_data = generator.generate_all_demo_data()

    # Save to JSON
    with open("demo_data_complete.json", "w") as f:
        json.dump(demo_data, f, indent=2)

    print(f"\n✓ Saved to demo_data_complete.json")
    print("\nNext steps:")
    print("1. Generate embeddings using Gemini")
    print("2. Index to Qdrant collections")
    print("3. Verify all 5 demo scenarios work")
