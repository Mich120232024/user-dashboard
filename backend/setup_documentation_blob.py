#!/usr/bin/env python3
"""
Setup Azure Blob Storage for documentation assets
Creates container and uploads structured documentation
"""
import os
import json
from pathlib import Path
from typing import Dict, List
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceExistsError

# Configuration
STORAGE_ACCOUNT_NAME = "contextstore1750317480"  # Using existing storage account
CONTAINER_NAME = "documentation-assets"
CONNECTION_STRING = None  # Will use DefaultAzureCredential if None

def get_blob_service_client():
    """Get Azure Blob Service Client using managed identity or connection string"""
    try:
        if CONNECTION_STRING:
            return BlobServiceClient.from_connection_string(CONNECTION_STRING)
        else:
            # Use DefaultAzureCredential for managed identity
            account_url = f"https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
            return BlobServiceClient(account_url, credential=DefaultAzureCredential())
    except Exception as e:
        print(f"Error creating blob service client: {e}")
        raise

def create_container(blob_service_client: BlobServiceClient):
    """Create the documentation-assets container"""
    try:
        container_client = blob_service_client.create_container(CONTAINER_NAME)
        print(f"✅ Created container: {CONTAINER_NAME}")
        return container_client
    except ResourceExistsError:
        print(f"✅ Container {CONTAINER_NAME} already exists")
        return blob_service_client.get_container_client(CONTAINER_NAME)
    except Exception as e:
        print(f"❌ Error creating container: {e}")
        raise

def upload_documentation_structure():
    """Upload documentation in structured format to Azure Blob Storage"""
    
    # Get blob service client
    blob_service_client = get_blob_service_client()
    
    # Create container
    container_client = create_container(blob_service_client)
    
    # Define documentation structure
    docs_base = Path(__file__).parent.parent / "docs"
    
    documentation_structure = {
        "messaging-system": {
            "category_name": "Messaging System",
            "description": "Complete messaging system documentation with CRUD operations and API reference",
            "files": [
                {
                    "local_path": docs_base / "MESSAGING_SYSTEM.md",
                    "blob_path": "messaging-system/messaging-system-guide.md",
                    "title": "Complete Messaging System Guide",
                    "description": "Comprehensive guide covering architecture, API endpoints, and usage patterns"
                }
            ]
        },
        "website-documentation": {
            "category_name": "Website Documentation", 
            "description": "User dashboard architecture and technical documentation",
            "files": [
                {
                    "local_path": docs_base / "WEBSITE_DOCUMENTATION.md",
                    "blob_path": "website-documentation/dashboard-architecture.md",
                    "title": "Dashboard Architecture Guide",
                    "description": "Complete architecture overview, security, and deployment documentation"
                }
            ]
        },
        "api-reference": {
            "category_name": "API Reference",
            "description": "Complete API documentation for all endpoints",
            "files": [
                {
                    "local_path": Path(__file__).parent / "api_endpoints.md",
                    "blob_path": "api-reference/fastapi-endpoints.md", 
                    "title": "FastAPI Endpoints Reference",
                    "description": "Complete reference for all API endpoints with examples"
                }
            ]
        },
        "deployment-guides": {
            "category_name": "Deployment Guides",
            "description": "Azure deployment and infrastructure setup guides",
            "files": []  # Will add deployment documentation
        },
        "architecture-diagrams": {
            "category_name": "Architecture Diagrams",
            "description": "Visual system architecture and data flow diagrams", 
            "files": []  # Will add when we create diagrams
        }
    }
    
    # Upload documentation files
    uploaded_files = []
    
    for category_key, category_info in documentation_structure.items():
        print(f"\n📁 Processing category: {category_info['category_name']}")
        
        for file_info in category_info["files"]:
            local_path = file_info["local_path"]
            blob_path = file_info["blob_path"]
            
            if local_path.exists():
                try:
                    # Read file content
                    with open(local_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add metadata header
                    metadata_header = f"""---
title: {file_info['title']}
description: {file_info['description']}
category: {category_info['category_name']}
last_updated: {local_path.stat().st_mtime}
source: {local_path.name}
---

"""
                    content_with_metadata = metadata_header + content
                    
                    # Upload to blob storage
                    blob_client = container_client.get_blob_client(blob_path)
                    blob_client.upload_blob(
                        content_with_metadata.encode('utf-8'),
                        overwrite=True,
                        metadata={
                            "title": file_info['title'],
                            "category": category_info['category_name'],
                            "description": file_info['description'],
                            "source_file": local_path.name
                        }
                    )
                    
                    uploaded_files.append({
                        "category": category_info['category_name'],
                        "title": file_info['title'],
                        "blob_path": blob_path,
                        "size": len(content_with_metadata),
                        "local_source": str(local_path)
                    })
                    
                    print(f"  ✅ Uploaded: {file_info['title']} -> {blob_path}")
                    
                except Exception as e:
                    print(f"  ❌ Error uploading {local_path}: {e}")
            else:
                print(f"  ⚠️  File not found: {local_path}")
    
    # Create and upload structure index
    structure_index = {
        "version": "1.0",
        "container": CONTAINER_NAME,
        "categories": []
    }
    
    for category_key, category_info in documentation_structure.items():
        category_files = [f for f in uploaded_files if f["category"] == category_info["category_name"]]
        
        if category_files:  # Only include categories with uploaded files
            structure_index["categories"].append({
                "name": category_info["category_name"],
                "path": category_key,
                "description": category_info["description"],
                "document_count": len(category_files),
                "documents": [
                    {
                        "name": f["title"],
                        "path": f["blob_path"],
                        "type": "markdown",
                        "size": f["size"]
                    }
                    for f in category_files
                ]
            })
    
    # Upload structure index
    try:
        index_blob = container_client.get_blob_client("structure.json")
        index_blob.upload_blob(
            json.dumps(structure_index, indent=2).encode('utf-8'),
            overwrite=True,
            metadata={"type": "structure_index", "version": "1.0"}
        )
        print(f"\n✅ Uploaded structure index: structure.json")
    except Exception as e:
        print(f"\n❌ Error uploading structure index: {e}")
    
    return uploaded_files, structure_index

def create_sample_deployment_doc():
    """Create a sample deployment documentation"""
    deployment_content = """# Azure Deployment Guide

## Overview
Complete guide for deploying the User Dashboard to Azure services.

## Prerequisites
- Azure subscription with appropriate permissions
- Azure CLI installed and configured
- Docker Desktop (for containerization)

## Services Used
- **Azure Container Instances** - For hosting the dashboard
- **Azure Cosmos DB** - Database backend  
- **Azure Blob Storage** - Documentation and assets
- **Azure Key Vault** - Secrets management

## Deployment Steps

### 1. Resource Group Setup
```bash
az group create --name user-dashboard-rg --location eastus
```

### 2. Cosmos DB Setup
```bash
az cosmosdb create --name user-dashboard-db --resource-group user-dashboard-rg
```

### 3. Container Registry
```bash
az acr create --name userdashboardregistry --resource-group user-dashboard-rg --sku Basic
```

### 4. Container Deployment
```bash
az container create --resource-group user-dashboard-rg --name user-dashboard \\
  --image userdashboardregistry.azurecr.io/dashboard:latest \\
  --ports 8080 --dns-name-label user-dashboard-prod
```

## Configuration
- Environment variables for Cosmos DB connection
- Key Vault integration for secrets
- CORS configuration for frontend-backend communication

## Monitoring
- Application Insights for performance monitoring
- Azure Monitor for infrastructure health
- Custom logging for application events

## Security
- Managed Identity for service-to-service authentication
- Network security groups for traffic control
- HTTPS enforcement with Azure Front Door
"""
    
    return deployment_content

def main():
    """Main execution function"""
    print("🚀 Setting up Azure Blob Storage for Documentation")
    print(f"📦 Storage Account: {STORAGE_ACCOUNT_NAME}")
    print(f"📁 Container: {CONTAINER_NAME}")
    
    try:
        # Upload existing documentation
        uploaded_files, structure = upload_documentation_structure()
        
        print(f"\n📊 Upload Summary:")
        print(f"   📝 Files uploaded: {len(uploaded_files)}")
        print(f"   📁 Categories: {len(structure['categories'])}")
        
        print(f"\n🔗 Container URL: https://{STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}")
        print(f"✅ Documentation setup complete!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)