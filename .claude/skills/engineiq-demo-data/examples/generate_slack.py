"""
Generate realistic Slack conversations for EngineIQ demo.

Creates threaded discussions with code snippets, mentions, and cross-references.
"""

import time
from typing import List, Dict


# Team members
USERS = {
    "alice": "Senior Engineer (K8s expert)",
    "bob": "DevOps Engineer",
    "charlie": "Full-Stack Developer",
    "diana": "Product Manager",
    "eve": "Backend Engineer",
    "frank": "Frontend Engineer",
    "grace": "Technical Architect",
    "henry": "SRE Engineer"
}

# Current timestamp for realistic dates
NOW = int(time.time())
DAY = 86400
HOUR = 3600


def create_slack_message(
    channel: str,
    user: str,
    text: str,
    timestamp: int,
    thread_ts: str = None,
    reactions: List[str] = None
) -> Dict:
    """Create a Slack message document"""
    msg_id = f"slack_{channel}_{timestamp}"

    return {
        "id": msg_id,
        "source": "slack",
        "content_type": "code" if "```" in text else "text",
        "file_type": "md",
        "title": f"#{channel} - {user}",
        "content": text,
        "url": f"https://techcorp.slack.com/archives/{channel}/p{str(timestamp).replace('.', '')}",
        "created_at": timestamp,
        "modified_at": timestamp,
        "owner": user,
        "contributors": [user],
        "permissions": {
            "public": channel in ["general", "engineering"],  # Some channels public
            "teams": ["engineering"],
            "users": [],
            "sensitivity": "internal",
            "offshore_restricted": False,
            "third_party_restricted": False
        },
        "metadata": {
            "slack_channel": channel,
            "slack_thread_ts": thread_ts,
            "slack_reactions": reactions or []
        },
        "tags": extract_tags(text),
        "language": "en"
    }


def extract_tags(text: str) -> List[str]:
    """Extract tags from message content"""
    tags = []
    keywords = {
        "kubernetes": ["kubernetes", "k8s", "kubectl", "pod", "deployment"],
        "docker": ["docker", "container", "image"],
        "deployment": ["deploy", "deployment", "release", "rollout"],
        "database": ["database", "db", "migration", "schema"],
        "incident": ["incident", "outage", "down", "error", "crash"]
    }

    text_lower = text.lower()
    for tag, keywords_list in keywords.items():
        if any(kw in text_lower for kw in keywords_list):
            tags.append(tag)

    return tags


def generate_deployment_thread() -> List[Dict]:
    """Scenario 1: Deployment discussion thread"""
    channel = "devops"
    base_ts = NOW - (7 * DAY)  # 7 days ago

    messages = []

    # Parent message
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="How do we safely deploy to production? I saw the deploy.py script in GitHub but not sure about the rollback process.",
        timestamp=base_ts,
        reactions=["thinking_face", "eyes"]
    ))

    # Reply 1
    messages.append(create_slack_message(
        channel=channel,
        user="bob",
        text="""Check out PR #456 - I added rollback logic there.
https://github.com/techcorp/deploybot/pull/456

Basically we keep the previous deployment config and can revert with:
```bash
kubectl rollout undo deployment/deploybot
```""",
        timestamp=base_ts + (3 * HOUR),
        thread_ts=str(base_ts),
        reactions=["white_check_mark"]
    ))

    # Reply 2
    messages.append(create_slack_message(
        channel=channel,
        user="charlie",
        text="""We also have a runbook in Confluence:
https://wiki.techcorp.com/production-deployment

It covers the full process including health checks and rollback procedures.""",
        timestamp=base_ts + (4 * HOUR),
        thread_ts=str(base_ts),
        reactions=["book"]
    ))

    # Reply 3
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="Perfect! One question - do we run database migrations before or after deploying the containers?",
        timestamp=base_ts + (5 * HOUR),
        thread_ts=str(base_ts)
    ))

    # Reply 4
    messages.append(create_slack_message(
        channel=channel,
        user="bob",
        text="""After deploying! The order is:
```python
# See deploy.py for full code
build_docker_image()
deploy_to_kubernetes()
run_migrations()  # <- After deployment
run_health_checks()
```

This way if migrations fail, we can rollback the deployment too.""",
        timestamp=base_ts + (5 * HOUR + 10 * 60),
        thread_ts=str(base_ts),
        reactions=["rocket", "+1"]
    ))

    return messages


def generate_incident_thread() -> List[Dict]:
    """Incident response thread (triggers Scenario 3 data)"""
    channel = "incidents"
    base_ts = NOW - (5 * DAY)  # 5 days ago

    messages = []

    # Incident start
    messages.append(create_slack_message(
        channel=channel,
        user="henry",
        text="""🚨 INCIDENT: Production pods crash looping after v2.3.1 deployment

Status: INVESTIGATING
Severity: P1 (customer impact)

Symptoms:
- All pods showing OOMKilled
- Health checks failing
- Users seeing 503 errors""",
        timestamp=base_ts,
        reactions=["rotating_light", "fire"]
    ))

    # Investigation
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="""Checking pod logs now...

```bash
kubectl logs deploybot-7d9f8-xk2p9 -n production

# Last lines:
java.lang.OutOfMemoryError: Java heap space
```

Memory limit is 512MB in deployment.yaml. App needs more.""",
        timestamp=base_ts + (10 * 60),
        thread_ts=str(base_ts)
    ))

    # Solution
    messages.append(create_slack_message(
        channel=channel,
        user="bob",
        text="""Heap dump analysis confirms we need 1GB.

I'm updating deployment.yaml and redeploying.

See JIRA: PROD-123""",
        timestamp=base_ts + (20 * 60),
        thread_ts=str(base_ts),
        reactions=["hammer_and_wrench"]
    ))

    # Resolution
    messages.append(create_slack_message(
        channel=channel,
        user="henry",
        text="""✅ RESOLVED

Duration: 45 minutes
Impact: ~5000 users saw errors

Next steps:
- Post-mortem doc in Box (alice writing)
- Update deployment runbook with memory requirements
- Add memory monitoring alerts""",
        timestamp=base_ts + (45 * 60),
        thread_ts=str(base_ts),
        reactions=["white_check_mark", "relieved"]
    ))

    return messages


def generate_kubernetes_qa_thread() -> List[Dict]:
    """K8s expertise demonstration (Scenario 4 data)"""
    channel = "kubernetes"
    base_ts = NOW - (3 * DAY)

    messages = []

    # Question 1
    messages.append(create_slack_message(
        channel=channel,
        user="charlie",
        text="How do I scale pods horizontally in production? Is it safe to do during business hours?",
        timestamp=base_ts,
        reactions=["question"]
    ))

    # Alice's expert answer
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="""Yes, horizontal scaling is safe during business hours! K8s handles it gracefully.

**Option 1: Manual scaling**
```bash
kubectl scale deployment/deploybot --replicas=5 -n production
```

**Option 2: Horizontal Pod Autoscaler (recommended)**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: deploybot-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: deploybot
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

K8s will gradually add pods (respecting PodDisruptionBudgets) so there's no downtime.

I wrote a guide in Confluence: https://wiki.techcorp.com/k8s-best-practices""",
        timestamp=base_ts + (15 * 60),
        thread_ts=str(base_ts),
        reactions=["star", "heart", "100"]
    ))

    # Follow-up question
    messages.append(create_slack_message(
        channel=channel,
        user="charlie",
        text="Thanks @alice! What about scaling down? Any gotchas?",
        timestamp=base_ts + (30 * 60),
        thread_ts=str(base_ts)
    ))

    # Alice's follow-up
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="""Good question! Main gotchas:

1. **Graceful shutdown**: Ensure your app handles SIGTERM
2. **PodDisruptionBudget**: Set minAvailable to prevent too many pods terminating
3. **Connection draining**: Give load balancer time to stop sending traffic

Example PDB:
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: deploybot-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: deploybot
```

This ensures at least 2 pods always running during scale-down.""",
        timestamp=base_ts + (40 * 60),
        thread_ts=str(base_ts),
        reactions=["raised_hands", "rocket"]
    ))

    return messages


def generate_db_migration_thread() -> List[Dict]:
    """Database migration question (Scenario 5: Knowledge gap)"""
    channel = "database"
    base_ts = NOW - (2 * DAY)

    messages = []

    # Question about rollback (knowledge gap)
    messages.append(create_slack_message(
        channel=channel,
        user="eve",
        text="How do we rollback database migrations if something goes wrong in production? I can't find docs on this.",
        timestamp=base_ts,
        reactions=["question", "thinking_face"]
    ))

    # Partial answer (inadequate)
    messages.append(create_slack_message(
        channel=channel,
        user="frank",
        text="I think there's a script in the repo... migration_tool.py? Not sure of the exact process though.",
        timestamp=base_ts + (1 * HOUR),
        thread_ts=str(base_ts)
    ))

    # Another person asking similar
    messages.append(create_slack_message(
        channel=channel,
        user="grace",
        text="I've been wondering this too! We really need a runbook for this. @alice do you know?",
        timestamp=base_ts + (2 * HOUR),
        thread_ts=str(base_ts),
        reactions=["eyes"]
    ))

    # Alice doesn't have full answer either
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="""There's partial info in the DB schema guide, but yeah we need a proper rollback runbook.

Basic idea:
1. Keep old schema version
2. Write reverse migrations
3. Test rollback in staging first

But we should document the full procedure. I'll add it to my TODO.""",
        timestamp=base_ts + (3 * HOUR),
        thread_ts=str(base_ts)
    ))

    return messages


def generate_architecture_discussion() -> List[Dict]:
    """Architecture discussion (Scenario 2 setup)"""
    channel = "engineering"
    base_ts = NOW - (20 * DAY)  # 20 days ago (early in project)

    messages = []

    # Grace shares architecture diagram
    messages.append(create_slack_message(
        channel=channel,
        user="grace",
        text="""I've created the system architecture diagram for DeployBot v1.0.

See Box: https://box.com/file/deploybot-architecture.png

Key components:
• API Gateway (Kong)
• Kubernetes cluster (3 nodes)
• PostgreSQL (RDS)
• Redis cache
• Prometheus + Grafana monitoring

Thoughts? Especially on the k8s setup.""",
        timestamp=base_ts,
        reactions=["eyes", "thinking_face"]
    ))

    # Alice's architectural feedback
    messages.append(create_slack_message(
        channel=channel,
        user="alice",
        text="""Looks good! A few suggestions for the k8s setup:

1. **Separate namespaces**: dev, staging, production
2. **Resource quotas**: Prevent one app from starving others
3. **Network policies**: Isolate workloads
4. **Horizontal pod autoscaling**: For the API pods

I'll write up best practices in Confluence and update the diagram with implementation details.""",
        timestamp=base_ts + (2 * HOUR),
        thread_ts=str(base_ts),
        reactions=["white_check_mark", "+1"]
    ))

    # Bob adds CI/CD perspective
    messages.append(create_slack_message(
        channel=channel,
        user="bob",
        text="""Also let's add the CI/CD pipeline to the diagram:

GitHub → CircleCI → Docker Hub → K8s

I'll create the deployment scripts and integrate with the architecture.

See Epic: PROD-100 in Jira""",
        timestamp=base_ts + (3 * HOUR),
        thread_ts=str(base_ts),
        reactions=["rocket"]
    ))

    return messages


def generate_all_slack_messages() -> List[Dict]:
    """Generate all Slack messages for demo"""
    all_messages = []

    # Scenario 1: Deployment discussion
    all_messages.extend(generate_deployment_thread())

    # Scenario 2: Architecture discussion
    all_messages.extend(generate_architecture_discussion())

    # Scenario 3: Incident (sensitive content context)
    all_messages.extend(generate_incident_thread())

    # Scenario 4: K8s expertise demonstration
    all_messages.extend(generate_kubernetes_qa_thread())

    # Scenario 5: DB migration knowledge gap
    all_messages.extend(generate_db_migration_thread())

    # Additional misc messages to reach ~60 total
    all_messages.extend(generate_misc_messages())

    print(f"Generated {len(all_messages)} Slack messages across channels")
    return all_messages


def generate_misc_messages() -> List[Dict]:
    """Additional messages for realism"""
    messages = []

    # Team announcements
    messages.append(create_slack_message(
        channel="general",
        user="diana",
        text="DeployBot v1.0 launches next week! Great work team 🎉",
        timestamp=NOW - (10 * DAY),
        reactions=["tada", "rocket", "clap"]
    ))

    # Code review request
    messages.append(create_slack_message(
        channel="devops",
        user="bob",
        text="PR ready for review: https://github.com/techcorp/deploybot/pull/489\n\nAdds health check improvements",
        timestamp=NOW - (4 * DAY),
        reactions=["eyes"]
    ))

    # Quick question
    messages.append(create_slack_message(
        channel="kubernetes",
        user="frank",
        text="What's the difference between ClusterIP and NodePort services?",
        timestamp=NOW - (6 * DAY)
    ))

    # Alice's answer
    messages.append(create_slack_message(
        channel="kubernetes",
        user="alice",
        text="""**ClusterIP**: Internal only, pods can reach it within cluster
**NodePort**: Exposes on each node's IP, accessible from outside

Use ClusterIP for internal services, NodePort for external (or better yet, LoadBalancer).""",
        timestamp=NOW - (6 * DAY - 10 * 60),
        thread_ts=str(NOW - (6 * DAY)),
        reactions=["white_check_mark"]
    ))

    return messages


if __name__ == "__main__":
    messages = generate_all_slack_messages()

    # Save to JSON for indexing
    import json
    with open("slack_messages.json", "w") as f:
        json.dump(messages, f, indent=2)

    print(f"\n✓ Saved {len(messages)} messages to slack_messages.json")

    # Show breakdown
    channels = {}
    for msg in messages:
        ch = msg["metadata"]["slack_channel"]
        channels[ch] = channels.get(ch, 0) + 1

    print("\nBreakdown by channel:")
    for ch, count in sorted(channels.items()):
        print(f"  #{ch}: {count} messages")
