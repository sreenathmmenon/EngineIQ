#!/usr/bin/env python3
"""
Remove owner field from wiki documents
"""

import sys
sys.path.insert(0, '.')

from backend.services.qdrant_service import QdrantService
from qdrant_client.models import Filter, FieldCondition, MatchValue

qdrant = QdrantService()

# Get all wiki documents
results = qdrant.client.scroll(
    collection_name="knowledge_base",
    scroll_filter=Filter(
        must=[
            FieldCondition(
                key="content_type",
                match=MatchValue(value="wiki")
            )
        ]
    ),
    limit=200,
    with_payload=True
)

points = results[0]
print(f"Found {len(points)} wiki documents")

# Update each point to remove owner
updated = 0
for point in points:
    if 'owner' in point.payload:
        # Create new payload without owner
        new_payload = {k: v for k, v in point.payload.items() if k != 'owner'}
        
        # Update point
        qdrant.client.set_payload(
            collection_name="knowledge_base",
            payload=new_payload,
            points=[point.id]
        )
        updated += 1

print(f"✅ Updated {updated} wiki documents (removed owner field)")
