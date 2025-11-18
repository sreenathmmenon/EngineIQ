"""
EngineIQ Slack Demo Data Generator

Generates realistic character-driven Slack conversations for demos.

Characters:
- Priya Sharma (junior, Bangalore, asks deployment questions)
- Sarah Chen (senior, SF, answers with expertise)
- Diego Fernández (K8s expert, Buenos Aires)
"""

import time
from typing import List, Dict


class SlackDemoDataGenerator:
    """Generate realistic Slack demo data with characters"""

    def __init__(self):
        self.characters = {
            "priya": {
                "id": "U001PRIYA",
                "name": "Priya Sharma",
                "role": "Junior Engineer",
                "location": "Bangalore, India",
                "expertise": ["python", "learning"],
            },
            "sarah": {
                "id": "U002SARAH",
                "name": "Sarah Chen",
                "role": "Senior Engineer",
                "location": "San Francisco, USA",
                "expertise": ["deployment", "cicd", "kubernetes", "architecture"],
            },
            "diego": {
                "id": "U003DIEGO",
                "name": "Diego Fernández",
                "role": "DevOps Lead",
                "location": "Buenos Aires, Argentina",
                "expertise": ["kubernetes", "infrastructure", "monitoring"],
            },
        }

        # Base timestamp (1 week ago)
        self.base_ts = int(time.time()) - (7 * 86400)

    def generate_all_messages(self) -> List[Dict]:
        """Generate all demo messages"""
        messages = []

        # Engineering channel messages
        messages.extend(self._generate_deployment_conversation())
        messages.extend(self._generate_kubernetes_discussion())
        messages.extend(self._generate_database_migration())

        # Confidential channel messages (triggers human-in-loop)
        messages.extend(self._generate_confidential_messages())

        return messages

    def _generate_deployment_conversation(self) -> List[Dict]:
        """Generate deployment Q&A conversation"""
        # Priya asks about deployment
        question_ts = str(self.base_ts + 1000)

        messages = [
            {
                "type": "message",
                "user": self.characters["priya"]["id"],
                "text": """Hey team! I'm trying to deploy our Python service to production for the first time. 
                
What's the recommended process? I've only done staging deploys before.

Any gotchas I should watch out for? 🤔""",
                "ts": question_ts,
                "thread_ts": question_ts,
                "reply_count": 2,
                "reactions": [
                    {"name": "eyes", "count": 3},
                    {"name": "thinking_face", "count": 1},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            # Sarah's expert answer
            {
                "type": "message",
                "user": self.characters["sarah"]["id"],
                "text": """Great question! Here's our production deployment checklist:

1. **Pre-deployment:**
   - Run full test suite: `pytest tests/ --cov=src`
   - Check migrations: `alembic upgrade head --sql`
   - Review recent PRs for breaking changes

2. **Deployment:**
```bash
# Tag the release
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3

# Deploy via CI/CD
./scripts/deploy.sh production
```

3. **Post-deployment:**
   - Monitor logs: `kubectl logs -f deployment/api-service`
   - Check metrics in Grafana
   - Verify health endpoint: `curl https://api.prod/health`

**Gotchas:**
- Always deploy during low-traffic hours (usually 2-4 AM PST)
- Have rollback plan ready
- Keep Slack open for alerts

Let me know if you need help with any step!""",
                "ts": str(float(question_ts) + 300),
                "thread_ts": question_ts,
                "reactions": [
                    {"name": "+1", "count": 5},
                    {"name": "heart", "count": 2},
                    {"name": "rocket", "count": 1},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            # Diego adds K8s specific tips
            {
                "type": "message",
                "user": self.characters["diego"]["id"],
                "text": """Adding to Sarah's excellent advice - for Kubernetes deployments:

**Zero-downtime deployment pattern:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0  # Keep all pods running
```

This ensures at least one pod is always available during rollout.

Also, always test in staging with production-like load first!""",
                "ts": str(float(question_ts) + 600),
                "thread_ts": question_ts,
                "reactions": [
                    {"name": "+1", "count": 4},
                    {"name": "kubernetes", "count": 2},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
        ]

        return messages

    def _generate_kubernetes_discussion(self) -> List[Dict]:
        """Generate Kubernetes troubleshooting discussion"""
        question_ts = str(self.base_ts + 10000)

        messages = [
            {
                "type": "message",
                "user": self.characters["priya"]["id"],
                "text": """Our pods keep crashing with OOMKilled status. Memory limit is set to 512Mi but usage shows 300Mi max. What could be causing this? 😰""",
                "ts": question_ts,
                "thread_ts": question_ts,
                "reply_count": 1,
                "reactions": [{"name": "eyes", "count": 2}],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            {
                "type": "message",
                "user": self.characters["diego"]["id"],
                "text": """This is usually a memory spike issue. Check these:

```bash
# 1. Check actual memory usage over time
kubectl top pods --containers

# 2. Look for memory leaks in logs
kubectl logs <pod-name> --previous | grep -i "memory\\|leak"

# 3. Increase limits with buffer
```

```yaml
resources:
  requests:
    memory: "256Mi"
  limits:
    memory: "768Mi"  # 1.5x-2x your average usage
```

**Pro tip:** Memory spikes often happen during:
- Application startup (loading data/models)
- Garbage collection pauses
- Cache invalidation

Set requests to average usage, limits to peak + buffer.

Also check if you have memory leaks - Python's `tracemalloc` module can help debug.""",
                "ts": str(float(question_ts) + 400),
                "thread_ts": question_ts,
                "reactions": [
                    {"name": "fire", "count": 3},
                    {"name": "+1", "count": 5},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
        ]

        return messages

    def _generate_database_migration(self) -> List[Dict]:
        """Generate database migration discussion"""
        message_ts = str(self.base_ts + 20000)

        messages = [
            {
                "type": "message",
                "user": self.characters["sarah"]["id"],
                "text": """Heads up team! We're running a database migration tonight at 11 PM PST.

**Migration:** Add `user_preferences` table and index on `users.email`

**Expected downtime:** 5-10 minutes

**Rollback plan:** 
```sql
-- If needed, run:
DROP TABLE user_preferences;
DROP INDEX idx_users_email;
```

I'll be online monitoring. Ping me if you see any issues!""",
                "ts": message_ts,
                "reactions": [
                    {"name": "eyes", "count": 8},
                    {"name": "white_check_mark", "count": 3},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
            {
                "type": "message",
                "user": self.characters["diego"]["id"],
                "text": """Migration completed successfully! ✅

- Duration: 4 minutes
- No errors
- All services back online
- Performance looks good

Database metrics looking healthy in Grafana.""",
                "ts": str(float(message_ts) + 3600),
                "reactions": [
                    {"name": "tada", "count": 5},
                    {"name": "rocket", "count": 3},
                ],
                "channel_id": "C001ENG",
                "channel_name": "engineering",
            },
        ]

        return messages

    def _generate_confidential_messages(self) -> List[Dict]:
        """Generate confidential channel messages (triggers approval)"""
        message_ts = str(self.base_ts + 30000)

        messages = [
            {
                "type": "message",
                "user": self.characters["sarah"]["id"],
                "text": """Payment processor integration update:

We've completed the Stripe API integration. New endpoints:
- POST /api/v1/payments/process
- GET /api/v1/payments/{id}/status

**Security notes:**
- All API keys stored in Vault
- PCI compliance checks passed
- Rate limiting: 100 req/min per user

Credentials for staging available in 1Password under "Payments Staging".""",
                "ts": message_ts,
                "reactions": [{"name": "lock", "count": 2}],
                "channel_id": "C002CONF",
                "channel_name": "confidential-payments",
            },
            {
                "type": "message",
                "user": self.characters["diego"]["id"],
                "text": """Added monitoring alerts for payment failures:

```yaml
alerts:
  - name: HighPaymentFailureRate
    expr: rate(payment_failures_total[5m]) > 0.1
    severity: critical
  
  - name: PaymentLatencyHigh  
    expr: payment_duration_seconds > 5
    severity: warning
```

Dashboard: https://grafana.internal/payments

Let's watch this closely for the first week.""",
                "ts": str(float(message_ts) + 7200),
                "reactions": [{"name": "+1", "count": 3}],
                "channel_id": "C002CONF",
                "channel_name": "confidential-payments",
            },
        ]

        return messages

    def get_mock_channels(self) -> List[Dict]:
        """Get mock channel list"""
        return [
            {
                "id": "C001ENG",
                "name": "engineering",
                "is_private": False,
                "context_team_id": "T001",
            },
            {
                "id": "C002CONF",
                "name": "confidential-payments",
                "is_private": True,
                "context_team_id": "T001",
            },
        ]

    def get_user_mapping(self) -> Dict[str, str]:
        """Get user ID to name mapping"""
        return {user["id"]: user["name"] for user in self.characters.values()}


# Example usage
if __name__ == "__main__":
    generator = SlackDemoDataGenerator()

    print("=== Slack Demo Data ===\n")

    messages = generator.generate_all_messages()
    print(f"Generated {len(messages)} messages")

    print(f"\nCharacters:")
    for char_id, char in generator.characters.items():
        print(f"  - {char['name']} ({char['role']}, {char['location']})")

    print(f"\nChannels:")
    for channel in generator.get_mock_channels():
        privacy = "Private" if channel["is_private"] else "Public"
        print(f"  - #{channel['name']} ({privacy})")

    print(f"\n=== Sample Message ===")
    sample = messages[0]
    print(f"Channel: #{sample['channel_name']}")
    print(f"User: {generator.get_user_mapping()[sample['user']]}")
    print(f"Text: {sample['text'][:100]}...")
