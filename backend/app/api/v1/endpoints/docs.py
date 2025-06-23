"""
Documentation endpoints for Azure Blob Storage integration
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse, Response
from azure.storage.blob import BlobServiceClient
from app.core.config import settings

router = APIRouter()

# Azure Blob Storage configuration
BLOB_ACCOUNT_NAME = "contextstore1750317480"
BLOB_CONTAINER_NAME = "documentation-assets"

def get_blob_client():
    """Get Azure Blob Storage client"""
    try:
        # Try to get connection string from settings/environment
        connection_string = getattr(settings, 'azure_storage_connection_string', None)
        if connection_string:
            return BlobServiceClient.from_connection_string(connection_string)
        else:
            # Fallback to managed identity with storage account name
            from azure.identity import DefaultAzureCredential
            account_url = f"https://{BLOB_ACCOUNT_NAME}.blob.core.windows.net"
            try:
                return BlobServiceClient(account_url, credential=DefaultAzureCredential())
            except Exception:
                return None
    except Exception:
        return None

@router.get("/structure")
async def get_documentation_structure() -> Dict[str, Any]:
    """
    Get documentation structure from Azure Blob Storage
    Falls back to local structure if Azure is unavailable
    """
    try:
        blob_client = get_blob_client()
        
        if blob_client:
            # Try to fetch structure from Azure Blob Storage
            try:
                container_client = blob_client.get_container_client(BLOB_CONTAINER_NAME)
                
                # First try to get documentation-structure.json
                try:
                    structure_blob = container_client.get_blob_client("documentation-structure.json")
                    structure_data = structure_blob.download_blob().readall().decode('utf-8')
                    structure = json.loads(structure_data)
                    structure["source"] = "azure_blob_index"
                    return structure
                except Exception:
                    # Try old structure.json
                    try:
                        structure_blob = container_client.get_blob_client("structure.json")
                        structure_data = structure_blob.download_blob().readall().decode('utf-8')
                        structure = json.loads(structure_data)
                        structure["source"] = "azure_blob_index_legacy"
                        return structure
                    except Exception:
                        # Fallback to listing blobs and organizing
                        blobs = container_client.list_blobs()
                        structure = organize_blob_structure(blobs)
                        return structure
                    
            except Exception as e:
                print(f"Azure Blob error: {e}")
                # Fall through to local fallback
        
        # Fallback to local documentation structure
        return get_local_documentation_structure()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documentation structure: {str(e)}")

def organize_blob_structure(blobs) -> Dict[str, Any]:
    """Organize blob list into categorized structure"""
    categories = {}
    
    for blob in blobs:
        # Parse blob path to determine category
        path_parts = blob.name.split('/')
        if len(path_parts) >= 2:
            category = path_parts[0]
            filename = path_parts[-1]
            
            if category not in categories:
                categories[category] = {
                    "name": category.replace('-', ' ').title(),
                    "path": category,
                    "documents": []
                }
            
            # Determine file type
            file_type = get_file_type(filename)
            
            categories[category]["documents"].append({
                "name": filename,
                "path": blob.name,
                "type": file_type,
                "size": blob.size if hasattr(blob, 'size') else 0,
                "last_modified": blob.last_modified.isoformat() if hasattr(blob, 'last_modified') else None
            })
    
    return {
        "categories": list(categories.values()),
        "source": "azure_blob"
    }

def get_local_documentation_structure() -> Dict[str, Any]:
    """Get local documentation structure as fallback"""
    # Get current documentation files
    docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
    
    # First try to read documentation-structure.json
    structure_file = docs_dir / "documentation-structure.json"
    if structure_file.exists():
        try:
            with open(structure_file, 'r', encoding='utf-8') as f:
                structure = json.load(f)
                structure["source"] = "local_structure_file"
                return structure
        except Exception as e:
            print(f"Error reading structure file: {e}")
    
    # Fallback to listing files
    local_docs = []
    
    if docs_dir.exists():
        for file_path in docs_dir.glob("*"):
            if file_path.is_file():
                local_docs.append({
                    "name": file_path.name,
                    "path": f"docs/{file_path.name}",
                    "type": get_file_type(file_path.name),
                    "size": file_path.stat().st_size,
                    "last_modified": None
                })
    
    # Check which docs actually exist
    messaging_exists = any("MESSAGING" in doc["name"] for doc in local_docs)
    website_exists = any("WEBSITE" in doc["name"] for doc in local_docs)
    
    return {
        "categories": [
            {
                "name": "Messaging System",
                "path": "messaging",
                "documents": [
                    {
                        "name": "Complete Messaging System Guide",
                        "path": "MESSAGING_SYSTEM.md",
                        "type": "markdown",
                        "description": "Comprehensive guide covering architecture, API endpoints, and usage patterns"
                    }
                ]
            },
            {
                "name": "Website Documentation",
                "path": "website", 
                "documents": [
                    {
                        "name": "Dashboard Architecture Guide", 
                        "path": "WEBSITE_DOCUMENTATION.md",
                        "type": "markdown",
                        "description": "Complete architecture overview, security, and deployment documentation"
                    }
                ]
            },
            {
                "name": "Local Documentation",
                "path": "local",
                "documents": local_docs
            }
        ],
        "source": "local_fallback"
    }

def get_file_type(filename: str) -> str:
    """Determine file type from extension"""
    extension = Path(filename).suffix.lower()
    
    type_mapping = {
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.txt': 'text',
        '.pdf': 'pdf',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.svg': 'image',
        '.html': 'html',
        '.css': 'css',
        '.js': 'javascript',
        '.py': 'python'
    }
    
    return type_mapping.get(extension, 'unknown')

@router.get("/content")
async def get_document_content(path: str = Query(..., description="Document path")):
    """
    Get document content from Azure Blob Storage or local files
    """
    try:
        # First try Azure Blob Storage
        blob_client = get_blob_client()
        
        if blob_client:
            try:
                blob_client_instance = blob_client.get_blob_client(
                    container=BLOB_CONTAINER_NAME, 
                    blob=path
                )
                
                # Download blob content
                blob_data = blob_client_instance.download_blob()
                content = blob_data.readall().decode('utf-8')
                
                return Response(
                    content=content,
                    media_type="text/plain",
                    headers={"X-Source": "azure_blob"}
                )
            except Exception as e:
                print(f"Azure Blob error for {path}: {e}")
                # Fall through to local fallback
        
        # Fallback to local files
        return await get_local_document_content(path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document content: {str(e)}")

async def get_local_document_content(path: str):
    """Get document content from local files"""
    try:
        # Get base docs directory 
        docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
        
        # Resolve local file path
        if path.startswith('docs/'):
            # Remove 'docs/' prefix and look in docs directory
            filename = path[5:]  # Remove 'docs/' prefix
            file_path = docs_dir / filename
        else:
            # Use the full path within docs directory
            file_path = docs_dir / path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="text/plain", 
            headers={"X-Source": "local_file"}
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")

@router.get("/download")
async def download_document(path: str = Query(..., description="Document path")):
    """
    Download document from Azure Blob Storage or local files
    """
    try:
        # First try Azure Blob Storage
        blob_client = get_blob_client()
        
        if blob_client:
            try:
                blob_client_instance = blob_client.get_blob_client(
                    container=BLOB_CONTAINER_NAME,
                    blob=path
                )
                
                # Get blob properties for filename
                blob_properties = blob_client_instance.get_blob_properties()
                filename = Path(path).name
                
                # Download blob content
                blob_data = blob_client_instance.download_blob()
                content = blob_data.readall()
                
                return Response(
                    content=content,
                    media_type="application/octet-stream",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}",
                        "X-Source": "azure_blob"
                    }
                )
            except Exception as e:
                print(f"Azure Blob download error for {path}: {e}")
                # Fall through to local fallback
        
        # Fallback to local files
        return await download_local_document(path)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

async def download_local_document(path: str):
    """Download document from local files"""
    try:
        # Get base docs directory (same as content function)
        docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
        
        # Resolve local file path
        if path.startswith('docs/'):
            # Remove 'docs/' prefix and look in docs directory
            filename = path[5:]  # Remove 'docs/' prefix
            file_path = docs_dir / filename
        else:
            # Use the full path within docs directory
            file_path = docs_dir / path
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Document not found: {path}")
        
        return FileResponse(
            path=str(file_path),
            filename=file_path.name,
            headers={"X-Source": "local_file"}
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

@router.post("/sync")
async def sync_documentation():
    """
    Sync local documentation to Azure Blob Storage
    This implements the maintenance requirement for documentation publication
    """
    try:
        blob_client = get_blob_client()
        
        if not blob_client:
            raise HTTPException(status_code=503, detail="Azure Blob Storage not available")
        
        container_client = blob_client.get_container_client(BLOB_CONTAINER_NAME)
        
        # Ensure container exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        # Sync local docs directory
        docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
        synced_files = []
        
        if docs_dir.exists():
            for file_path in docs_dir.rglob("*"):
                if file_path.is_file():
                    # Calculate relative path for blob name
                    relative_path = file_path.relative_to(docs_dir.parent)
                    blob_name = str(relative_path).replace('\\', '/')
                    
                    # Upload file to blob storage
                    with open(file_path, 'rb') as data:
                        blob_client_instance = container_client.get_blob_client(blob_name)
                        blob_client_instance.upload_blob(data, overwrite=True)
                    
                    synced_files.append({
                        "local_path": str(file_path),
                        "blob_path": blob_name,
                        "size": file_path.stat().st_size
                    })
        
        return {
            "status": "success",
            "synced_files": len(synced_files),
            "files": synced_files,
            "container": BLOB_CONTAINER_NAME
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing documentation: {str(e)}")

@router.get("/debug")
async def debug_paths():
    """Debug path resolution"""
    try:
        docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
        return {
            "current_file": str(Path(__file__)),
            "docs_dir_path": str(docs_dir),
            "docs_exists": docs_dir.exists(),
            "docs_contents": [f.name for f in docs_dir.glob("*")] if docs_dir.exists() else [],
            "resolved_path": str(docs_dir.resolve())
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/health")
async def check_documentation_health():
    """
    Check documentation system health
    """
    try:
        blob_client = get_blob_client()
        azure_available = blob_client is not None
        
        # Check local documentation
        docs_dir = Path(__file__).parent.parent.parent.parent.parent.parent / "docs"
        local_docs_count = len(list(docs_dir.glob("*"))) if docs_dir.exists() else 0
        
        # Check Azure Blob if available
        azure_docs_count = 0
        if azure_available:
            try:
                container_client = blob_client.get_container_client(BLOB_CONTAINER_NAME)
                blobs = list(container_client.list_blobs())
                azure_docs_count = len(blobs)
            except Exception:
                azure_available = False
        
        return {
            "status": "healthy",
            "azure_blob_available": azure_available,
            "local_docs_count": local_docs_count,
            "azure_docs_count": azure_docs_count,
            "documentation_source": "azure_blob" if azure_available else "local_fallback"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "documentation_source": "local_fallback"
        }