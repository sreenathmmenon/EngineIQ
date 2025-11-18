#!/usr/bin/env python3
"""
Create sample technical PDFs for demonstration
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def create_aws_deployment_guide():
    """Create a comprehensive AWS deployment guide PDF"""
    
    filename = "AWS_Kubernetes_Deployment_Guide.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story = []
    
    # Title
    story.append(Paragraph("AWS Kubernetes Deployment Guide", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Introduction
    story.append(Paragraph("Introduction", styles['Heading1']))
    story.append(Paragraph("""
    This comprehensive guide covers best practices for deploying Kubernetes clusters on Amazon Web Services (AWS). 
    It includes step-by-step instructions for setting up EKS (Elastic Kubernetes Service), configuring networking,
    implementing security best practices, and managing production workloads.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    # Chapter 1
    story.append(Paragraph("Chapter 1: EKS Cluster Setup", styles['Heading1']))
    story.append(Paragraph("""
    Amazon EKS makes it easy to deploy, manage, and scale containerized applications using Kubernetes on AWS.
    This chapter covers the initial setup process.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Prerequisites", styles['Heading2']))
    story.append(Paragraph("""
    • AWS Account with appropriate IAM permissions<br/>
    • AWS CLI installed and configured<br/>
    • kubectl command-line tool<br/>
    • eksctl command-line utility<br/>
    • Basic understanding of Kubernetes concepts
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Creating the Cluster", styles['Heading2']))
    story.append(Paragraph("""
    Use eksctl to create a new cluster with managed node groups. This is the recommended approach for production workloads.
    """, styles['BodyText']))
    story.append(Paragraph("""
    <pre>
    eksctl create cluster \\
      --name production-cluster \\
      --version 1.27 \\
      --region us-west-2 \\
      --nodegroup-name standard-workers \\
      --node-type t3.large \\
      --nodes 3 \\
      --nodes-min 1 \\
      --nodes-max 4 \\
      --managed
    </pre>
    """, styles['Code']))
    
    story.append(PageBreak())
    
    # Chapter 2
    story.append(Paragraph("Chapter 2: Networking Configuration", styles['Heading1']))
    story.append(Paragraph("""
    Proper networking configuration is crucial for security and performance. This chapter covers VPC setup,
    subnet configuration, and load balancer integration.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("VPC and Subnet Design", styles['Heading2']))
    story.append(Paragraph("""
    For production deployments, use a dedicated VPC with both public and private subnets across multiple
    availability zones. This provides high availability and allows for proper isolation of resources.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Load Balancer Setup", styles['Heading2']))
    story.append(Paragraph("""
    AWS Load Balancer Controller enables you to create Application Load Balancers (ALB) and Network Load Balancers (NLB)
    for your Kubernetes services. Install it using Helm:
    """, styles['BodyText']))
    story.append(Paragraph("""
    <pre>
    helm repo add eks https://aws.github.io/eks-charts
    helm install aws-load-balancer-controller eks/aws-load-balancer-controller \\
      --set clusterName=production-cluster \\
      --set serviceAccount.create=false \\
      --set serviceAccount.name=aws-load-balancer-controller
    </pre>
    """, styles['Code']))
    
    story.append(PageBreak())
    
    # Chapter 3
    story.append(Paragraph("Chapter 3: Security Best Practices", styles['Heading1']))
    story.append(Paragraph("""
    Security should be a top priority when deploying Kubernetes on AWS. This chapter covers IAM roles,
    pod security policies, secrets management, and network policies.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("IAM Roles for Service Accounts", styles['Heading2']))
    story.append(Paragraph("""
    IRSA (IAM Roles for Service Accounts) allows you to associate IAM roles with Kubernetes service accounts.
    This provides fine-grained permissions for your applications without using static credentials.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Secrets Management", styles['Heading2']))
    story.append(Paragraph("""
    Use AWS Secrets Manager or AWS Systems Manager Parameter Store to store sensitive information.
    The Kubernetes External Secrets Operator can sync these secrets into your cluster automatically.
    """, styles['BodyText']))
    
    story.append(PageBreak())
    
    # Chapter 4
    story.append(Paragraph("Chapter 4: Monitoring and Logging", styles['Heading1']))
    story.append(Paragraph("""
    Comprehensive monitoring and logging are essential for maintaining healthy production systems.
    This chapter covers CloudWatch integration, Prometheus, and centralized logging.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("CloudWatch Container Insights", styles['Heading2']))
    story.append(Paragraph("""
    Container Insights provides cluster, node, and pod-level metrics. Enable it to get visibility
    into your cluster's performance and resource utilization.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Prometheus and Grafana", styles['Heading2']))
    story.append(Paragraph("""
    Deploy Prometheus for metrics collection and Grafana for visualization. The kube-prometheus-stack
    Helm chart provides a complete monitoring solution.
    """, styles['BodyText']))
    
    story.append(PageBreak())
    
    # Appendix
    story.append(Paragraph("Appendix: Troubleshooting Guide", styles['Heading1']))
    story.append(Paragraph("""
    Common issues and their solutions:
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Node Not Ready", styles['Heading2']))
    story.append(Paragraph("""
    If nodes show as NotReady, check:
    • VPC CNI plugin is running correctly
    • Node has network connectivity
    • Sufficient resources available
    • Security groups allow required traffic
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Pod Pending State", styles['Heading2']))
    story.append(Paragraph("""
    If pods remain in Pending state:
    • Check resource requests vs available capacity
    • Verify node selectors and taints/tolerations
    • Review pod security policies
    • Check for persistent volume binding issues
    """, styles['BodyText']))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Created {filename} ({os.path.getsize(filename) / 1024:.1f} KB)")
    return filename


def create_database_migration_guide():
    """Create a database migration guide PDF"""
    
    filename = "Database_Migration_Best_Practices.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Database Migration Best Practices", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Introduction
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    story.append(Paragraph("""
    Database migrations are critical operations that require careful planning and execution.
    This guide provides comprehensive best practices for planning, executing, and validating
    database migrations in production environments.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.3*inch))
    
    # Chapter 1
    story.append(Paragraph("Chapter 1: Migration Planning", styles['Heading1']))
    story.append(Paragraph("""
    Proper planning is essential for successful database migrations. This includes schema analysis,
    dependency mapping, and rollback strategy development.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Schema Analysis", styles['Heading2']))
    story.append(Paragraph("""
    Before starting a migration:
    • Document all schema changes required
    • Identify foreign key constraints and indexes
    • Map data type conversions
    • Estimate data volume and transfer time
    • Plan for downtime or zero-downtime approach
    """, styles['BodyText']))
    
    story.append(PageBreak())
    
    # Chapter 2
    story.append(Paragraph("Chapter 2: Blue-Green Deployment", styles['Heading1']))
    story.append(Paragraph("""
    Blue-green deployment is a technique that reduces downtime and risk by running two identical
    production environments. This chapter explains how to implement this pattern for database migrations.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Implementation Steps", styles['Heading2']))
    story.append(Paragraph("""
    1. Set up the new (green) environment with the updated schema
    2. Configure dual-write to both blue and green databases
    3. Migrate historical data to green environment
    4. Verify data consistency between environments
    5. Switch read traffic to green environment
    6. Monitor for issues
    7. Decommission blue environment after validation period
    """, styles['BodyText']))
    
    story.append(PageBreak())
    
    # Chapter 3
    story.append(Paragraph("Chapter 3: Rollback Procedures", styles['Heading1']))
    story.append(Paragraph("""
    Every migration must have a tested rollback plan. This chapter covers creating and testing
    rollback scripts before production deployment.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Rollback Script Template", styles['Heading2']))
    story.append(Paragraph("""
    <pre>
    -- Rollback script for Migration-2024-001
    BEGIN TRANSACTION;
    
    -- Step 1: Verify current state
    SELECT COUNT(*) FROM new_table;
    
    -- Step 2: Restore old schema
    ALTER TABLE users DROP COLUMN new_field;
    
    -- Step 3: Restore constraints
    ALTER TABLE users ADD CONSTRAINT old_constraint CHECK (condition);
    
    -- Step 4: Verify rollback
    SELECT * FROM users WHERE id = 1;
    
    COMMIT;
    </pre>
    """, styles['Code']))
    
    story.append(PageBreak())
    
    # Chapter 4
    story.append(Paragraph("Chapter 4: Testing and Validation", styles['Heading1']))
    story.append(Paragraph("""
    Comprehensive testing is crucial for migration success. This includes staging validation,
    performance testing, and data integrity checks.
    """, styles['BodyText']))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Validation Checklist", styles['Heading2']))
    story.append(Paragraph("""
    • Row counts match between old and new schemas
    • Data types converted correctly
    • Foreign keys and indexes created successfully
    • Query performance meets SLAs
    • Application integration tests pass
    • Backup and restore procedures verified
    """, styles['BodyText']))
    
    # Build PDF
    doc.build(story)
    print(f"✅ Created {filename} ({os.path.getsize(filename) / 1024:.1f} KB)")
    return filename


if __name__ == "__main__":
    print("Creating sample technical PDFs...")
    print()
    
    try:
        pdf1 = create_aws_deployment_guide()
        pdf2 = create_database_migration_guide()
        
        print()
        print("✅ Sample PDFs created successfully!")
        print(f"   • {pdf1}")
        print(f"   • {pdf2}")
        
    except Exception as e:
        print(f"❌ Error creating PDFs: {e}")
        print("Install reportlab: pip install reportlab")
