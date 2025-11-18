#!/usr/bin/env python3
"""
Quick script to process GitHub wiki pages
"""

import sys
import os
sys.path.insert(0, '.')

from backend.services.gemini_service import GeminiService
from backend.services.qdrant_service import QdrantService
from qdrant_client.models import PointStruct
import uuid
import time

def process_wiki_page(title: str, content: str, repo_url: str, gemini: GeminiService, qdrant: QdrantService):
    """Process a single wiki page"""
    
    # Generate embedding
    embedding = gemini.generate_embedding(content)
    
    # Create point
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            "title": title,
            "content": content[:1000],  # First 1000 chars
            "raw_content": content,
            "source": "GitHub",
            "content_type": "wiki",
            "url": repo_url,
            "indexed_at": int(time.time()),
            "owner": "Community",
        }
    )
    
    # Index to Qdrant
    qdrant.client.upsert(
        collection_name="knowledge_base",
        points=[point],
        wait=True
    )
    
    print(f"✅ Indexed: {title}")
    return True


def main():
    print("="*70)
    print("🔷 GitHub Wiki Processor")
    print("="*70)
    
    # Initialize services
    gemini = GeminiService()
    qdrant = QdrantService()
    
    # Sample wiki pages (Kubernetes basics)
    wiki_pages = [
        {
            "title": "Kubernetes: What is Kubernetes?",
            "url": "https://github.com/kubernetes/kubernetes/wiki",
            "content": """
# What is Kubernetes?

Kubernetes (K8s) is an open-source system for automating deployment, scaling, and management of containerized applications.

## Key Features

### Container Orchestration
Kubernetes groups containers that make up an application into logical units for easy management and discovery. It automatically places containers based on their resource requirements and other constraints.

### Self-Healing
Kubernetes restarts containers that fail, replaces containers, kills containers that don't respond to user-defined health checks, and doesn't advertise them to clients until they are ready to serve.

### Horizontal Scaling
Scale your application up and down with a simple command, with a UI, or automatically based on CPU usage.

### Service Discovery and Load Balancing
Kubernetes can expose a container using the DNS name or using their own IP address. If traffic to a container is high, Kubernetes is able to load balance and distribute the network traffic.

### Automated Rollouts and Rollbacks
You can describe the desired state for your deployed containers using Kubernetes, and it can change the actual state to the desired state at a controlled rate.

### Storage Orchestration
Kubernetes allows you to automatically mount a storage system of your choice, such as local storage, public cloud providers, and more.

## Architecture

Kubernetes follows a master-worker architecture:

### Control Plane (Master)
- API Server: Frontend for the Kubernetes control plane
- Scheduler: Assigns pods to nodes
- Controller Manager: Runs controller processes
- etcd: Consistent and highly-available key-value store

### Worker Nodes
- Kubelet: Agent that runs on each node
- Container Runtime: Software responsible for running containers (Docker, containerd)
- Kube-proxy: Network proxy running on each node

## Core Concepts

### Pods
The smallest deployable units in Kubernetes. A pod represents a single instance of a running process in your cluster.

### Services
An abstract way to expose an application running on a set of pods as a network service.

### Deployments
Provides declarative updates for pods and ReplicaSets. You describe a desired state in a Deployment, and the Deployment Controller changes the actual state to the desired state.

### ConfigMaps and Secrets
ConfigMaps allow you to decouple configuration artifacts from image content. Secrets are similar but designed to hold sensitive information.

### Namespaces
Kubernetes supports multiple virtual clusters backed by the same physical cluster. These virtual clusters are called namespaces.

## Use Cases

1. **Microservices Architecture**: Deploy and manage microservices efficiently
2. **CI/CD Pipelines**: Automate deployment pipelines
3. **Hybrid Cloud**: Run applications across on-premises and cloud environments
4. **Machine Learning**: Manage ML workloads and training jobs
5. **Batch Processing**: Run batch jobs and scheduled tasks
"""
        },
        {
            "title": "Kubernetes: Pod Networking",
            "url": "https://github.com/kubernetes/kubernetes/wiki/Networking",
            "content": """
# Kubernetes Networking

Kubernetes networking addresses four concerns:
- Containers within a Pod use networking to communicate via loopback
- Cluster networking provides communication between different Pods
- The Service resource lets you expose an application running in Pods
- You can also use Services to publish services only for consumption inside your cluster

## Network Model

Kubernetes imposes the following fundamental requirements on any networking implementation:

### Requirements
1. **All pods can communicate with all other pods** without NAT
2. **All nodes can communicate with all pods** without NAT
3. **The IP that a pod sees itself as** is the same IP that others see it as

## Pod-to-Pod Communication

Every pod gets its own IP address. This means you do not need to explicitly create links between pods and you almost never need to deal with mapping container ports to host ports.

### Within the Same Node
Pods on a node can communicate with all pods on all nodes without NAT via a virtual network interface.

### Across Nodes
The network must route packets between pods on different nodes. This is typically implemented using:
- Overlay networks (Flannel, Weave)
- Layer 3 routing (Calico)
- Cloud provider networking (AWS VPC, Azure VNET)

## Services and Load Balancing

Services provide a stable IP address and DNS name for a set of pods. Types:

### ClusterIP (default)
Exposes the service on an internal IP in the cluster. Only reachable from within the cluster.

### NodePort
Exposes the service on each Node's IP at a static port. A ClusterIP service is automatically created.

### LoadBalancer
Exposes the service externally using a cloud provider's load balancer. NodePort and ClusterIP services are automatically created.

### ExternalName
Maps the service to a DNS name by returning a CNAME record.

## DNS

Kubernetes offers a DNS cluster addon Service that automatically assigns DNS names to services.

### Service DNS
Services get DNS names like: `my-service.my-namespace.svc.cluster.local`

### Pod DNS
Pods get DNS names based on their IP: `172-17-0-3.default.pod.cluster.local`

## Network Policies

NetworkPolicies allow you to control traffic flow at the IP address or port level. By default, pods are non-isolated and accept traffic from any source.

Example policy:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend
```

## Ingress

Ingress exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. Traffic routing is controlled by rules defined on the Ingress resource.

Benefits:
- Load balancing
- SSL termination
- Name-based virtual hosting
"""
        },
        {
            "title": "Kubernetes: Storage Concepts",
            "url": "https://github.com/kubernetes/kubernetes/wiki/Storage",
            "content": """
# Kubernetes Storage

Kubernetes storage abstracts the details of how storage is provided from how it is consumed.

## Volumes

A Volume is a directory, possibly with some data in it, which is accessible to containers in a pod.

### Volume Types

#### emptyDir
An empty directory created when a pod is assigned to a node. Exists as long as the pod runs on that node.

#### hostPath
Mounts a file or directory from the host node's filesystem into your pod.

#### persistentVolumeClaim
Used to mount a PersistentVolume into a pod.

#### configMap
Provides a way to inject configuration data into pods.

#### secret
Used to pass sensitive information to pods.

#### nfs
Allows an existing NFS (Network File System) share to be mounted into a pod.

## Persistent Volumes (PV)

A PersistentVolume (PV) is a piece of storage in the cluster that has been provisioned by an administrator or dynamically provisioned using Storage Classes.

### Lifecycle

1. **Provisioning**: Either static (admin creates PVs) or dynamic (using StorageClass)
2. **Binding**: PVC is bound to a PV
3. **Using**: Pod uses the PVC as a volume
4. **Reclaiming**: When PVC is deleted, PV can be retained, recycled, or deleted

### Access Modes

- ReadWriteOnce (RWO): Volume can be mounted as read-write by a single node
- ReadOnlyMany (ROX): Volume can be mounted as read-only by many nodes
- ReadWriteMany (RWX): Volume can be mounted as read-write by many nodes

## Persistent Volume Claims (PVC)

A PersistentVolumeClaim (PVC) is a request for storage by a user. Claims can request specific size and access modes.

Example:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 8Gi
  storageClassName: fast
```

## Storage Classes

A StorageClass provides a way to describe the "classes" of storage offered. Different classes might map to:
- Quality-of-service levels
- Backup policies
- Arbitrary policies determined by administrators

### Dynamic Provisioning

When none of the static PVs match a PVC, the cluster may try to dynamically provision a volume for the PVC based on StorageClass.

### Common Provisioners

- AWS EBS: kubernetes.io/aws-ebs
- Azure Disk: kubernetes.io/azure-disk
- GCE PD: kubernetes.io/gce-pd
- NFS: kubernetes.io/nfs
- Ceph RBD: kubernetes.io/rbd

## StatefulSets

StatefulSets are designed for stateful applications that require:
- Stable, unique network identifiers
- Stable, persistent storage
- Ordered, graceful deployment and scaling
- Ordered, automated rolling updates

Each pod in a StatefulSet gets a persistent identifier and a stable hostname.

## Best Practices

1. **Use PVCs instead of PVs directly** in pod specifications
2. **Define StorageClasses** for different performance tiers
3. **Set resource requests and limits** for storage
4. **Use StatefulSets** for applications that need stable storage
5. **Implement backup strategies** for critical data
6. **Monitor storage metrics** and set up alerts
"""
        }
    ]
    
    # Process each page
    success_count = 0
    for page in wiki_pages:
        try:
            if process_wiki_page(
                title=page["title"],
                content=page["content"],
                repo_url=page["url"],
                gemini=gemini,
                qdrant=qdrant
            ):
                success_count += 1
        except Exception as e:
            print(f"❌ Failed to process {page['title']}: {e}")
    
    print("\n" + "="*70)
    print(f"✅ Successfully indexed {success_count}/{len(wiki_pages)} wiki pages")
    print("="*70)


if __name__ == "__main__":
    main()
