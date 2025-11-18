"""
GitHub Demo Data - Character-Driven Examples

Realistic GitHub data featuring:
- Sarah Chen (47 commits on deployment scripts, K8s configs)
- Diego Fernández (31 commits on K8s, mostly in Spanish comments)
- Priya Sharma (recent commits, learning deployment)

Repos: backend-api, deployment-scripts, infrastructure
Code in: Python, Bash, YAML (K8s configs)
"""

import time
from typing import Dict, List

# Demo characters
CHARACTERS = {
    "sarah_chen": {
        "login": "sarahchen",
        "name": "Sarah Chen",
        "commits": 47,
        "expertise": ["deployment", "kubernetes", "python", "bash"]
    },
    "diego_fernandez": {
        "login": "diegofernandez",
        "name": "Diego Fernández",
        "commits": 31,
        "expertise": ["kubernetes", "infrastructure", "yaml"]
    },
    "priya_sharma": {
        "login": "priyasharma",
        "name": "Priya Sharma",
        "commits": 8,
        "expertise": ["learning", "deployment"]
    }
}

# Demo repositories
DEMO_REPOS = {
    "backend-api": {
        "full_name": "engineiq/backend-api",
        "description": "Main backend API service",
        "language": "Python",
        "private": False,
        "stars": 42,
        "forks": 8,
    },
    "deployment-scripts": {
        "full_name": "engineiq/deployment-scripts",
        "description": "Deployment automation scripts",
        "language": "Shell",
        "private": False,
        "stars": 15,
        "forks": 3,
    },
    "infrastructure": {
        "full_name": "engineiq/infrastructure",
        "description": "Kubernetes infrastructure configs",
        "language": "YAML",
        "private": False,
        "stars": 23,
        "forks": 5,
    }
}

# Demo code files
DEMO_FILES = [
    # Sarah Chen's deployment script
    {
        "repo": "deployment-scripts",
        "path": "deploy_production.py",
        "content": '''#!/usr/bin/env python3
"""
Production deployment script for EngineIQ
Author: Sarah Chen
"""

import subprocess
import sys
import argparse
from typing import List, Dict

class ProductionDeployer:
    """Handle production deployments with safety checks"""
    
    def __init__(self, namespace: str = "production"):
        self.namespace = namespace
        self.kubectl = "kubectl"
    
    def check_cluster_health(self) -> bool:
        """Verify cluster is healthy before deployment"""
        try:
            result = subprocess.run(
                [self.kubectl, "get", "nodes"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Check all nodes are Ready
            lines = result.stdout.split('\\n')
            for line in lines[1:]:
                if line and "NotReady" in line:
                    print(f"❌ Node not ready: {line}")
                    return False
            
            print("✓ All cluster nodes are healthy")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking cluster health: {e}")
            return False
    
    def backup_current_deployment(self, service: str) -> bool:
        """Create backup of current deployment"""
        try:
            backup_file = f"{service}-backup-{int(time.time())}.yaml"
            
            result = subprocess.run(
                [
                    self.kubectl, "get", "deployment", service,
                    "-n", self.namespace,
                    "-o", "yaml"
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            with open(backup_file, 'w') as f:
                f.write(result.stdout)
            
            print(f"✓ Backed up deployment to {backup_file}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Backup failed: {e}")
            return False
    
    def apply_manifest(self, manifest_path: str) -> bool:
        """Apply Kubernetes manifest"""
        try:
            subprocess.run(
                [
                    self.kubectl, "apply",
                    "-f", manifest_path,
                    "-n", self.namespace
                ],
                check=True
            )
            
            print(f"✓ Applied manifest: {manifest_path}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to apply manifest: {e}")
            return False
    
    def wait_for_rollout(self, service: str, timeout: int = 300) -> bool:
        """Wait for deployment rollout to complete"""
        try:
            subprocess.run(
                [
                    self.kubectl, "rollout", "status",
                    f"deployment/{service}",
                    "-n", self.namespace,
                    f"--timeout={timeout}s"
                ],
                check=True
            )
            
            print(f"✓ Deployment rolled out successfully: {service}")
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Rollout failed: {e}")
            return False
    
    def deploy(self, manifest: str, service: str) -> bool:
        """Execute full deployment workflow"""
        print(f"\\n🚀 Starting deployment: {service}")
        print("=" * 50)
        
        # Safety checks
        if not self.check_cluster_health():
            print("❌ Cluster health check failed. Aborting.")
            return False
        
        # Backup
        self.backup_current_deployment(service)
        
        # Deploy
        if not self.apply_manifest(manifest):
            print("❌ Manifest application failed. Aborting.")
            return False
        
        # Wait for rollout
        if not self.wait_for_rollout(service):
            print("❌ Rollout failed. Consider rolling back.")
            return False
        
        print("\\n✅ Deployment completed successfully!")
        return True

def main():
    parser = argparse.ArgumentParser(description="Deploy to production")
    parser.add_argument("manifest", help="Path to Kubernetes manifest")
    parser.add_argument("service", help="Service name")
    parser.add_argument("--namespace", default="production", help="Kubernetes namespace")
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(namespace=args.namespace)
    success = deployer.deploy(args.manifest, args.service)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
''',
        "language": "python",
        "author": "sarahchen",
        "contributors": ["sarahchen", "priyasharma"],
        "commits": 12,
    },
    
    # Diego's Kubernetes deployment config with Spanish comments
    {
        "repo": "infrastructure",
        "path": "k8s/backend-deployment.yaml",
        "content": '''# Deployment configuration para Backend API
# Autor: Diego Fernández
# Última actualización: 2024-03-15

apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: production
  labels:
    app: backend-api
    version: v2.1.0
    team: platform
spec:
  replicas: 3  # Tres réplicas para alta disponibilidad
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Sin downtime durante deployment
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
        version: v2.1.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: backend-api-sa
      
      # Init container para database migrations
      initContainers:
      - name: db-migration
        image: engineiq/backend-api:v2.1.0
        command: ["python", "manage.py", "migrate"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
      
      containers:
      - name: api
        image: engineiq/backend-api:v2.1.0
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        
        # Variables de entorno
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-credentials
              key: api-key
        
        # Health checks - importante para rolling updates
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        # Recursos - ajustados después de load testing
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          runAsNonRoot: true
          runAsUser: 1000
          capabilities:
            drop:
            - ALL
      
      # Affinity rules - distribuir pods en diferentes nodes
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchLabels:
                  app: backend-api
              topologyKey: kubernetes.io/hostname

---
# Service para exponer el backend
apiVersion: v1
kind: Service
metadata:
  name: backend-api
  namespace: production
  labels:
    app: backend-api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: backend-api
''',
        "language": "yaml",
        "author": "diegofernandez",
        "contributors": ["diegofernandez", "sarahchen"],
        "commits": 23,
    },
    
    # Priya's recent contribution - learning deployment
    {
        "repo": "deployment-scripts",
        "path": "rollback.sh",
        "content": '''#!/bin/bash
# Emergency rollback script
# Author: Priya Sharma (with help from Sarah Chen)
# Created: 2024-03-20

set -e  # Exit on error
set -u  # Exit on undefined variable

# Configuration
NAMESPACE="${NAMESPACE:-production}"
SERVICE="${1:-}"

if [ -z "$SERVICE" ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 backend-api"
    exit 1
fi

echo "🔄 Rolling back deployment: $SERVICE"
echo "Namespace: $NAMESPACE"
echo ""

# Get current revision
echo "Checking current revision..."
CURRENT=$(kubectl get deployment "$SERVICE" -n "$NAMESPACE" -o jsonpath='{.metadata.annotations.deployment\\.kubernetes\\.io/revision}')
echo "Current revision: $CURRENT"

# Calculate previous revision
if [ "$CURRENT" -gt 1 ]; then
    PREVIOUS=$((CURRENT - 1))
    echo "Rolling back to revision: $PREVIOUS"
else
    echo "❌ Error: No previous revision found"
    exit 1
fi

# Confirm rollback
echo ""
read -p "Are you sure you want to rollback $SERVICE to revision $PREVIOUS? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled"
    exit 0
fi

# Execute rollback
echo ""
echo "Executing rollback..."
kubectl rollout undo deployment/"$SERVICE" -n "$NAMESPACE" --to-revision="$PREVIOUS"

# Wait for rollback to complete
echo ""
echo "Waiting for rollback to complete..."
kubectl rollout status deployment/"$SERVICE" -n "$NAMESPACE" --timeout=300s

# Verify pods are running
echo ""
echo "Verifying pods..."
kubectl get pods -n "$NAMESPACE" -l app="$SERVICE"

echo ""
echo "✅ Rollback completed successfully!"
echo ""
echo "Next steps:"
echo "1. Monitor application health"
echo "2. Check logs: kubectl logs -n $NAMESPACE -l app=$SERVICE --tail=50"
echo "3. Investigate root cause of the issue"
echo "4. Update runbook with lessons learned"
''',
        "language": "bash",
        "author": "priyasharma",
        "contributors": ["priyasharma", "sarahchen"],
        "commits": 3,
    },
]

# Demo pull requests
DEMO_PULL_REQUESTS = [
    {
        "repo": "deployment-scripts",
        "number": 42,
        "title": "Add health checks to deployment script",
        "state": "closed",
        "merged": True,
        "author": "sarahchen",
        "body": """## Changes
- Added cluster health checks before deployment
- Added backup functionality
- Improved error handling and rollback safety

## Testing
- Tested on staging environment
- Verified rollback works correctly
- Load tested with 1000 req/s

## Deployment Impact
No breaking changes. Adds safety checks that will prevent bad deployments.

Closes #156
""",
        "comments": [
            {
                "author": "diegofernandez",
                "body": "Excelente trabajo! Los health checks son muy importantes. ¿Consideraste agregar un timeout configurable para el rollout?",
            },
            {
                "author": "sarahchen",
                "body": "Good point! I'll add that in the next iteration. For now, it's hardcoded to 5 minutes which should be enough for most cases.",
            },
            {
                "author": "priyasharma",
                "body": "This is great! I learned a lot from reading this code. Can we add more comments explaining the kubectl commands?",
            },
            {
                "author": "sarahchen",
                "body": "@priyasharma Good suggestion! I'll add more documentation in the README.",
            },
        ],
        "review_comments": [
            {
                "author": "diegofernandez",
                "path": "deploy_production.py",
                "body": "Consider using kubectl wait instead of rollout status for more control",
            },
        ],
    },
    {
        "repo": "infrastructure",
        "number": 67,
        "title": "Update K8s resource limits based on load testing",
        "state": "open",
        "merged": False,
        "author": "diegofernandez",
        "body": """## Cambios
Después de hacer load testing en staging, actualicé los resource limits:

- Memory request: 256Mi → 512Mi (vimos OOM kills con 256Mi)
- CPU limit: 500m → 1000m (CPU throttling bajo carga)
- Agregué readiness probe más agresivo

## Resultados de Testing
- Sin OOM kills con 512Mi bajo carga de 2000 req/s
- Sin CPU throttling con 1000m limit
- Tiempo de respuesta p99: 150ms → 85ms

## Referencias
- Load testing results: https://grafana.example.com/d/load-test-2024-03-18
- Memory profiling: attached memory_profile.png
""",
        "comments": [
            {
                "author": "sarahchen",
                "body": "Great work on the load testing! These numbers look much better. Have you checked the cost impact of the increased resources?",
            },
            {
                "author": "diegofernandez",
                "body": "Sí, revisé con el equipo de finanzas. El incremento es aproximadamente $150/mes pero evitamos los OOM kills que causaban downtime.",
            },
        ],
        "review_comments": [],
    },
]

# Demo issues
DEMO_ISSUES = [
    {
        "repo": "deployment-scripts",
        "number": 156,
        "title": "Add pre-deployment health checks",
        "state": "closed",
        "author": "priyasharma",
        "body": """## Problem
We had a production deployment fail last week because one of the K8s nodes was in NotReady state. The deployment script didn't check cluster health before deploying.

## Proposed Solution
Add health checks to verify:
1. All nodes are Ready
2. Required pods are running
3. Sufficient resources available

## Impact
This would prevent deployments to unhealthy clusters and save us from incidents.
""",
        "comments": [
            {
                "author": "sarahchen",
                "body": "Good catch! I'll take this one. We definitely need better pre-deployment validation.",
            },
            {
                "author": "diegofernandez",
                "body": "También deberíamos verificar que no hay deployments en progreso antes de iniciar uno nuevo.",
            },
            {
                "author": "sarahchen",
                "body": "Agreed! I'll add that check as well.",
            },
            {
                "author": "priyasharma",
                "body": "Thank you @sarahchen! Let me know if I can help with testing.",
            },
        ],
    },
    {
        "repo": "infrastructure",
        "number": 203,
        "title": "Document disaster recovery procedures",
        "state": "open",
        "author": "sarahchen",
        "body": """## Context
We need comprehensive disaster recovery documentation for our K8s infrastructure.

## Required Documentation
1. Backup procedures for:
   - etcd snapshots
   - Persistent volume backups
   - Configuration secrets
   
2. Restore procedures:
   - Complete cluster rebuild from backups
   - Individual service restoration
   - Data recovery from PV snapshots

3. Runbooks for common failure scenarios:
   - Node failures
   - Zone outages  
   - Complete cluster failure

## Owner
@sarahchen will coordinate, but need input from @diegofernandez on infrastructure specifics.
""",
        "comments": [
            {
                "author": "diegofernandez",
                "body": "Estoy de acuerdo que esto es prioritario. Puedo documentar los procedimientos de backup de etcd que tenemos automatizados.",
            },
            {
                "author": "priyasharma",
                "body": "I can help document the PV backup process. I just learned about Velero in the training.",
            },
        ],
    },
]

def get_demo_data() -> Dict:
    """Get all demo data in a structured format"""
    return {
        "characters": CHARACTERS,
        "repositories": DEMO_REPOS,
        "files": DEMO_FILES,
        "pull_requests": DEMO_PULL_REQUESTS,
        "issues": DEMO_ISSUES,
    }
