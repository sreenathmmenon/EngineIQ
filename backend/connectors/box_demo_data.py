"""
EngineIQ Box Demo Data Generator

Generates realistic Box files showcasing Gemini multimodal capabilities.
Includes PDFs, images, documents with various sensitivity levels.
"""

import time
from typing import List, Dict
import base64


class BoxDemoDataGenerator:
    """Generate realistic Box demo data with multimodal files"""

    def __init__(self):
        self.base_ts = int(time.time()) - (30 * 86400)  # 30 days ago

        # Demo folders
        self.folders = {
            "engineering_docs": {
                "id": "folder_001",
                "name": "Engineering",
                "path": "/Engineering/Docs/",
            },
            "finance_confidential": {
                "id": "folder_002",
                "name": "Finance",
                "path": "/Finance/Confidential/",
            },
            "hr_policies": {
                "id": "folder_003",
                "name": "HR",
                "path": "/HR/Policies/",
            },
            "architecture": {
                "id": "folder_004",
                "name": "Architecture",
                "path": "/Engineering/Architecture/",
            },
        }

    def generate_all_files(self) -> List[Dict]:
        """Generate all demo files"""
        files = []

        # Engineering files
        files.append(self._generate_deployment_runbook())
        files.append(self._generate_database_migration_guide())

        # Architecture diagrams (images)
        files.append(self._generate_payment_architecture_diagram())
        files.append(self._generate_k8s_cluster_diagram())

        # Finance files (confidential)
        files.append(self._generate_q4_financial_strategy())
        files.append(self._generate_compensation_analysis())

        # HR policies
        files.append(self._generate_remote_work_policy())

        return files

    def _generate_deployment_runbook(self) -> Dict:
        """Generate deployment runbook PDF (multimodal parsing)"""
        return {
            "id": "file_001",
            "name": "Deployment_Runbook_v2.3.pdf",
            "type": "file",
            "size": 245000,
            "created_at": self.base_ts + 1000,
            "modified_at": self.base_ts + 50000,
            "folder": self.folders["engineering_docs"],
            "content_type": "pdf",
            "file_type": "pdf",
            "owner": "sarah.chen@engineiq.com",
            "shared_users": [
                "sarah.chen@engineiq.com",
                "diego.fernandez@engineiq.com",
                "priya.sharma@engineiq.com",
            ],
            "is_public": False,
            "tags": ["deployment", "runbook", "production", "documentation"],
            "comments": [
                {
                    "user": "diego.fernandez@engineiq.com",
                    "text": "Great documentation! Added some K8s specific notes in v2.2",
                    "created_at": self.base_ts + 30000,
                },
                {
                    "user": "priya.sharma@engineiq.com",
                    "text": "This helped me with my first prod deployment. Thanks!",
                    "created_at": self.base_ts + 45000,
                },
            ],
            "raw_content": b"""DEPLOYMENT RUNBOOK v2.3

=== Pre-Deployment Checklist ===

1. Code Review
   - All PRs approved by 2+ reviewers
   - CI/CD pipeline green
   - Security scan passed

2. Database Migrations
   - Review migration scripts
   - Test on staging
   - Prepare rollback scripts

3. Infrastructure
   - Check resource capacity
   - Verify monitoring alerts
   - Update DNS if needed

=== Deployment Steps ===

1. Create release tag:
   $ git tag -a v1.2.3 -m "Release 1.2.3"
   $ git push origin v1.2.3

2. Deploy to staging:
   $ ./deploy.sh staging v1.2.3

3. Run smoke tests:
   $ pytest tests/smoke/ -v

4. Deploy to production:
   $ ./deploy.sh production v1.2.3

5. Monitor for 15 minutes:
   - Check error rates in Grafana
   - Monitor response times
   - Verify health endpoints

=== Rollback Procedure ===

If issues detected:
1. Immediately rollback:
   $ kubectl rollout undo deployment/api-service

2. Notify team in #incidents channel

3. Investigate and fix before retry

=== Post-Deployment ===

- Update changelog
- Notify stakeholders
- Monitor for 24 hours
- Document any issues

[Diagram: Deployment pipeline architecture - see page 5]
[Diagram: Rollback decision tree - see page 8]
""",
            "mock_gemini_result": {
                "text": "DEPLOYMENT RUNBOOK v2.3...",
                "image_descriptions": [
                    "Diagram showing CI/CD pipeline: GitHub → Jenkins → Staging → Production with rollback paths",
                    "Decision tree flowchart for rollback: Monitor errors → Threshold exceeded → Auto-rollback",
                ],
                "topics": ["deployment", "devops", "kubernetes", "ci/cd"],
            },
        }

    def _generate_database_migration_guide(self) -> Dict:
        """Generate database migration guide DOCX"""
        return {
            "id": "file_002",
            "name": "Database Migration Guide.docx",
            "type": "file",
            "size": 87000,
            "created_at": self.base_ts + 2000,
            "modified_at": self.base_ts + 40000,
            "folder": self.folders["engineering_docs"],
            "content_type": "text",
            "file_type": "docx",
            "owner": "sarah.chen@engineiq.com",
            "shared_users": [
                "sarah.chen@engineiq.com",
                "diego.fernandez@engineiq.com",
            ],
            "is_public": False,
            "tags": ["database", "migration", "postgresql", "best-practices"],
            "comments": [
                {
                    "user": "diego.fernandez@engineiq.com",
                    "text": "Added section on zero-downtime migrations",
                    "created_at": self.base_ts + 35000,
                }
            ],
            "raw_content": """DATABASE MIGRATION GUIDE

Overview:
This guide covers best practices for database schema migrations in our PostgreSQL databases.

Best Practices:

1. Always test migrations on staging first
2. Create rollback scripts before deployment
3. Use transactions where possible
4. Monitor query performance after migration
5. Schedule migrations during low-traffic periods

Zero-Downtime Migration Pattern:

For adding new columns:
1. Add column as nullable
2. Deploy code that writes to new column
3. Backfill existing data
4. Make column non-nullable
5. Remove old column in next migration

Example:
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
-- Deploy code
UPDATE users SET email_verified = TRUE WHERE email IS NOT NULL;
ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL;

Tools:
- Alembic for Python apps
- Flyway for Java apps
- Manual SQL for complex changes

Always document your migrations!
""",
            "mock_gemini_result": None,  # Plain text, no special processing
        }

    def _generate_payment_architecture_diagram(self) -> Dict:
        """Generate payment system architecture diagram (Gemini Vision)"""
        return {
            "id": "file_003",
            "name": "Payment_System_Architecture.png",
            "type": "file",
            "size": 523000,
            "created_at": self.base_ts + 5000,
            "modified_at": self.base_ts + 5000,
            "folder": self.folders["architecture"],
            "content_type": "image",
            "file_type": "png",
            "owner": "sarah.chen@engineiq.com",
            "shared_users": [
                "sarah.chen@engineiq.com",
                "diego.fernandez@engineiq.com",
            ],
            "is_public": False,
            "tags": ["architecture", "payments", "system-design", "stripe"],
            "comments": [],
            "raw_content": b"<mock image data>",  # Would be actual PNG bytes
            "mock_gemini_result": {
                "type": "architecture_diagram",
                "main_components": [
                    "API Gateway",
                    "Payment Service",
                    "Stripe Integration",
                    "Database",
                    "Message Queue",
                    "Webhook Handler",
                ],
                "concepts": [
                    "microservices",
                    "event-driven",
                    "payment-processing",
                    "retry-logic",
                    "idempotency",
                ],
                "semantic_description": """Architecture diagram showing payment system flow:

1. Client requests hit API Gateway
2. Payment Service validates and processes requests
3. Stripe API integration handles actual payment processing
4. Results stored in PostgreSQL database
5. RabbitMQ message queue for async processing
6. Webhook handler receives Stripe callbacks
7. Retry logic with exponential backoff for failed payments

Key features:
- Idempotency keys prevent duplicate charges
- Transaction logs for auditing
- Circuit breaker pattern for Stripe API
- Rate limiting (100 requests/minute per user)

Components are deployed as separate Kubernetes pods with auto-scaling.
""",
            },
        }

    def _generate_k8s_cluster_diagram(self) -> Dict:
        """Generate Kubernetes cluster diagram (Gemini Vision)"""
        return {
            "id": "file_004",
            "name": "K8s_Cluster_Overview.png",
            "type": "file",
            "size": 678000,
            "created_at": self.base_ts + 10000,
            "modified_at": self.base_ts + 15000,
            "folder": self.folders["architecture"],
            "content_type": "image",
            "file_type": "png",
            "owner": "diego.fernandez@engineiq.com",
            "shared_users": ["diego.fernandez@engineiq.com", "sarah.chen@engineiq.com"],
            "is_public": False,
            "tags": ["kubernetes", "infrastructure", "devops", "cloud"],
            "comments": [
                {
                    "user": "sarah.chen@engineiq.com",
                    "text": "Is the staging cluster on GKE or EKS?",
                    "created_at": self.base_ts + 12000,
                },
                {
                    "user": "diego.fernandez@engineiq.com",
                    "text": "Staging is on GKE. Production uses multi-region EKS.",
                    "created_at": self.base_ts + 13000,
                },
            ],
            "raw_content": b"<mock image data>",
            "mock_gemini_result": {
                "type": "infrastructure_diagram",
                "main_components": [
                    "Ingress Controller",
                    "API Pods (3 replicas)",
                    "Worker Pods (5 replicas)",
                    "Redis Cache",
                    "PostgreSQL (managed)",
                    "Prometheus/Grafana",
                    "Cert Manager",
                ],
                "concepts": [
                    "kubernetes",
                    "high-availability",
                    "auto-scaling",
                    "monitoring",
                    "load-balancing",
                ],
                "semantic_description": """Kubernetes cluster architecture diagram showing:

Production Cluster (us-east-1):
- 3 master nodes (managed by EKS)
- 10 worker nodes (auto-scaling 5-20)
- Ingress: NGINX ingress controller with SSL termination
- Services:
  - API service: 3 pods, HPA target 70% CPU
  - Worker service: 5 pods, processing background jobs
  - Redis: 3-node cluster for caching
  - PostgreSQL: RDS Multi-AZ for HA
  
Monitoring:
- Prometheus collects metrics from all pods
- Grafana dashboards for visualization
- Alertmanager sends alerts to PagerDuty

Storage:
- EBS volumes for persistent data
- S3 for file storage
- ECR for container images

Networking:
- VPC with private subnets for pods
- NAT gateway for outbound traffic
- Application Load Balancer at edge

The diagram shows traffic flow from external clients through ALB → Ingress → Services → Pods.
""",
            },
        }

    def _generate_q4_financial_strategy(self) -> Dict:
        """Generate Q4 financial strategy PDF (CONFIDENTIAL - triggers approval)"""
        return {
            "id": "file_005",
            "name": "Q4_Financial_Strategy.pdf",
            "type": "file",
            "size": 1500000,
            "created_at": self.base_ts + 20000,
            "modified_at": self.base_ts + 25000,
            "folder": self.folders["finance_confidential"],
            "content_type": "pdf",
            "file_type": "pdf",
            "owner": "cfo@engineiq.com",
            "shared_users": ["cfo@engineiq.com", "ceo@engineiq.com"],
            "is_public": False,
            "tags": ["confidential", "financial", "strategy", "Q4"],
            "comments": [],
            "raw_content": b"""Q4 FINANCIAL STRATEGY - CONFIDENTIAL

Executive Summary:
Revenue targets, cost optimization, and growth initiatives for Q4 2024.

Revenue Projections:
- Q4 Target: $5.2M (15% growth YoY)
- New customer acquisition: 50 enterprise deals
- Expansion revenue: $800K from existing customers

Cost Optimization:
- Infrastructure: Migrate to reserved instances (-20% cloud costs)
- Headcount: Strategic hiring in engineering and sales
- Marketing: Focus on high-ROI channels

Investment Areas:
1. Product development: AI features ($500K)
2. Sales team expansion: 5 new AEs ($400K)
3. Infrastructure scaling: Multi-region deployment ($300K)

Risk Factors:
- Economic uncertainty
- Competition from larger players
- Customer churn in enterprise segment

[Charts and financial projections on pages 3-7]
""",
            "mock_gemini_result": {
                "text": "Q4 FINANCIAL STRATEGY - CONFIDENTIAL...",
                "image_descriptions": [
                    "Bar chart showing quarterly revenue projections: Q1 $3.8M, Q2 $4.1M, Q3 $4.5M, Q4 $5.2M",
                    "Pie chart of cost breakdown: Engineering 45%, Sales 25%, Marketing 15%, Operations 15%",
                    "Line graph of customer acquisition trends with forecast through Q4",
                ],
                "topics": ["finance", "strategy", "revenue", "projections"],
            },
        }

    def _generate_compensation_analysis(self) -> Dict:
        """Generate compensation analysis spreadsheet (RESTRICTED)"""
        return {
            "id": "file_006",
            "name": "2024_Compensation_Analysis_RESTRICTED.xlsx",
            "type": "file",
            "size": 456000,
            "created_at": self.base_ts + 30000,
            "modified_at": self.base_ts + 32000,
            "folder": self.folders["finance_confidential"],
            "content_type": "text",
            "file_type": "xlsx",
            "owner": "hr@engineiq.com",
            "shared_users": ["hr@engineiq.com", "cfo@engineiq.com"],
            "is_public": False,
            "tags": ["restricted", "compensation", "hr", "confidential"],
            "comments": [],
            "raw_content": """2024 COMPENSATION ANALYSIS - RESTRICTED

Department-level compensation data and market benchmarks.

Engineering:
- Average base: $145K
- Market 50th percentile: $138K
- Equity grants: 0.05% - 0.15%

Sales:
- Average base: $95K
- Average OTE: $180K
- Commission structure: 10% on ARR

Product:
- Average base: $135K
- Market competitive
- Annual bonus pool: 15% of salary

Benefits:
- Health insurance: $12K/employee/year
- 401k match: 4%
- PTO: 25 days

Market Analysis:
Compared to Radford, Pave, and Carta data.
Recommendations for 2024 compensation adjustments.
""",
            "mock_gemini_result": None,
        }

    def _generate_remote_work_policy(self) -> Dict:
        """Generate remote work policy document (PUBLIC)"""
        return {
            "id": "file_007",
            "name": "Remote_Work_Policy_2024.pdf",
            "type": "file",
            "size": 234000,
            "created_at": self.base_ts + 35000,
            "modified_at": self.base_ts + 36000,
            "folder": self.folders["hr_policies"],
            "content_type": "pdf",
            "file_type": "pdf",
            "owner": "hr@engineiq.com",
            "shared_users": [],  # Available to all employees
            "is_public": True,
            "tags": ["policy", "remote-work", "hr", "guidelines"],
            "comments": [
                {
                    "user": "priya.sharma@engineiq.com",
                    "text": "Great policy! Appreciate the flexibility.",
                    "created_at": self.base_ts + 36500,
                }
            ],
            "raw_content": b"""REMOTE WORK POLICY 2024

EngineIQ supports flexible work arrangements.

Eligibility:
- All full-time employees
- Must have manager approval
- Equipment provided by company

Guidelines:

1. Work Hours:
   - Core hours: 10 AM - 4 PM local time
   - Flexible start/end times
   - Must be available for meetings

2. Communication:
   - Slack for daily communication
   - Video on for team meetings
   - Update status regularly

3. Equipment:
   - Laptop provided
   - Monitor and peripherals (up to $500)
   - Internet stipend: $50/month

4. Workspace:
   - Dedicated workspace required
   - Must meet security requirements
   - Regular home office assessments

5. Travel:
   - Quarterly team offsites
   - Annual company retreat
   - Travel expenses covered

This policy applies globally with local variations.
""",
            "mock_gemini_result": {
                "text": "REMOTE WORK POLICY 2024...",
                "image_descriptions": [],
                "topics": ["hr", "remote-work", "policy", "benefits"],
            },
        }

    def get_mock_folders(self) -> List[Dict]:
        """Get mock folder list"""
        return list(self.folders.values())


# Example usage
if __name__ == "__main__":
    generator = BoxDemoDataGenerator()

    print("=== Box Demo Data ===\n")

    files = generator.generate_all_files()
    print(f"Generated {len(files)} files")

    print(f"\nFolders:")
    for folder in generator.get_mock_folders():
        print(f"  - {folder['path']} ({folder['name']})")

    print(f"\n=== Files by Type ===")
    for content_type in ["pdf", "image", "text"]:
        type_files = [f for f in files if f["content_type"] == content_type]
        print(f"\n{content_type.upper()} ({len(type_files)} files):")
        for file in type_files:
            sensitivity = "CONFIDENTIAL" if "confidential" in file["name"].lower() or "restricted" in file["name"].lower() else "PUBLIC"
            print(f"  - {file['name']} ({sensitivity})")

    print(f"\n=== Multimodal Files (Showcase Gemini) ===")
    multimodal = [f for f in files if f["content_type"] in ["pdf", "image"]]
    for file in multimodal:
        print(f"\n{file['name']}:")
        print(f"  Type: {file['content_type']}")
        print(f"  Folder: {file['folder']['path']}")
        if file["mock_gemini_result"]:
            if "image_descriptions" in file["mock_gemini_result"]:
                print(f"  Images: {len(file['mock_gemini_result']['image_descriptions'])}")
            print(f"  Topics: {', '.join(file['mock_gemini_result'].get('topics', []))}")
