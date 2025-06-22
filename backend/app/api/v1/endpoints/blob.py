"""Azure Blob Storage endpoints for FastAPI backend."""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class BlobInfo(BaseModel):
    name: str
    size: int
    last_modified: datetime
    content_type: Optional[str] = None
    etag: str

class ContainerInfo(BaseModel):
    name: str
    blob_count: int
    total_size: int
    last_modified: Optional[datetime] = None

class BlobUploadRequest(BaseModel):
    container_name: str
    blob_name: str
    content: str
    content_type: Optional[str] = "text/plain"
    overwrite: bool = True

# Azure Blob Storage client
blob_service_client = None

def get_blob_service_client():
    """Get Azure Blob Storage client."""
    global blob_service_client
    if blob_service_client is None:
        if not AZURE_AVAILABLE:
            raise HTTPException(status_code=500, detail="Azure SDK not available")
        
        # Get connection string from environment
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            raise HTTPException(status_code=500, detail="Azure Storage connection string not configured")
        
        try:
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to Azure Storage")
    
    return blob_service_client

@router.get("/containers")
async def list_containers():
    """List all blob storage containers."""
    try:
        client = get_blob_service_client()
        containers = []
        
        for container in client.list_containers():
            # Get blob count and total size
            container_client = client.get_container_client(container.name)
            blob_count = 0
            total_size = 0
            last_modified = None
            
            for blob in container_client.list_blobs():
                blob_count += 1
                total_size += blob.size or 0
                if not last_modified or blob.last_modified > last_modified:
                    last_modified = blob.last_modified
            
            containers.append(ContainerInfo(
                name=container.name,
                blob_count=blob_count,
                total_size=total_size,
                last_modified=last_modified
            ))
        
        return {
            'success': True,
            'containers': [c.dict() for c in containers]
        }
        
    except Exception as e:
        logger.error(f"Error listing containers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_name}")
async def create_container(container_name: str):
    """Create a new blob storage container."""
    try:
        client = get_blob_service_client()
        container_client = client.get_container_client(container_name)
        
        try:
            container_client.create_container()
            return {
                'success': True,
                'message': f'Container {container_name} created successfully'
            }
        except ResourceExistsError:
            return {
                'success': True,
                'message': f'Container {container_name} already exists'
            }
        
    except Exception as e:
        logger.error(f"Error creating container {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_name}/blobs")
async def list_blobs(
    container_name: str,
    prefix: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000)
):
    """List blobs in a container."""
    try:
        client = get_blob_service_client()
        container_client = client.get_container_client(container_name)
        
        blobs = []
        blob_iter = container_client.list_blobs(name_starts_with=prefix)
        
        for i, blob in enumerate(blob_iter):
            if i >= limit:
                break
                
            blobs.append(BlobInfo(
                name=blob.name,
                size=blob.size or 0,
                last_modified=blob.last_modified,
                content_type=blob.content_settings.content_type if blob.content_settings else None,
                etag=blob.etag
            ))
        
        return {
            'success': True,
            'container': container_name,
            'blobs': [b.dict() for b in blobs],
            'count': len(blobs)
        }
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Container {container_name} not found")
    except Exception as e:
        logger.error(f"Error listing blobs in {container_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_name}/blobs/{blob_name}")
async def get_blob(container_name: str, blob_name: str):
    """Download a blob."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        # Get blob properties
        properties = blob_client.get_blob_properties()
        
        # Download blob content
        blob_data = blob_client.download_blob()
        content = blob_data.readall()
        
        # Determine content type
        content_type = properties.content_settings.content_type or "application/octet-stream"
        
        return StreamingResponse(
            BytesIO(content),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={blob_name}",
                "Content-Length": str(len(content)),
                "ETag": properties.etag,
                "Last-Modified": properties.last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
            }
        )
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Blob {blob_name} not found in container {container_name}")
    except Exception as e:
        logger.error(f"Error downloading blob {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_name}/blobs/{blob_name}/content")
async def get_blob_content(container_name: str, blob_name: str, as_text: bool = Query(True)):
    """Get blob content as text or JSON."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        # Download blob content
        blob_data = blob_client.download_blob()
        content = blob_data.readall()
        
        if as_text:
            try:
                text_content = content.decode('utf-8')
                
                # Try to parse as JSON if possible
                try:
                    json_content = json.loads(text_content)
                    return {
                        'success': True,
                        'content': json_content,
                        'content_type': 'json',
                        'size': len(content)
                    }
                except:
                    return {
                        'success': True,
                        'content': text_content,
                        'content_type': 'text',
                        'size': len(content)
                    }
            except UnicodeDecodeError:
                return {
                    'success': False,
                    'error': 'Cannot decode blob as text'
                }
        else:
            return {
                'success': True,
                'content': content.hex(),
                'content_type': 'binary',
                'size': len(content)
            }
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Blob {blob_name} not found in container {container_name}")
    except Exception as e:
        logger.error(f"Error getting blob content {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_name}/blobs/{blob_name}")
async def upload_blob_text(container_name: str, blob_name: str, upload_request: BlobUploadRequest):
    """Upload text content to a blob."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        # Upload content
        blob_client.upload_blob(
            upload_request.content.encode('utf-8'),
            content_settings={'content_type': upload_request.content_type},
            overwrite=upload_request.overwrite
        )
        
        return {
            'success': True,
            'message': f'Blob {blob_name} uploaded successfully',
            'url': blob_client.url
        }
        
    except ResourceExistsError:
        raise HTTPException(status_code=409, detail=f"Blob {blob_name} already exists and overwrite is False")
    except Exception as e:
        logger.error(f"Error uploading blob {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/containers/{container_name}/blobs/{blob_name}/upload")
async def upload_blob_file(
    container_name: str, 
    blob_name: str, 
    file: UploadFile = File(...),
    overwrite: bool = Form(True)
):
    """Upload a file to a blob."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        # Read file content
        content = await file.read()
        
        # Upload content
        blob_client.upload_blob(
            content,
            content_settings={'content_type': file.content_type},
            overwrite=overwrite
        )
        
        return {
            'success': True,
            'message': f'File {file.filename} uploaded as blob {blob_name}',
            'size': len(content),
            'content_type': file.content_type,
            'url': blob_client.url
        }
        
    except ResourceExistsError:
        raise HTTPException(status_code=409, detail=f"Blob {blob_name} already exists and overwrite is False")
    except Exception as e:
        logger.error(f"Error uploading file to blob {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/containers/{container_name}/blobs/{blob_name}")
async def delete_blob(container_name: str, blob_name: str):
    """Delete a blob."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        blob_client.delete_blob()
        
        return {
            'success': True,
            'message': f'Blob {blob_name} deleted successfully'
        }
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Blob {blob_name} not found in container {container_name}")
    except Exception as e:
        logger.error(f"Error deleting blob {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/containers/{container_name}/blobs/{blob_name}/properties")
async def get_blob_properties(container_name: str, blob_name: str):
    """Get blob properties and metadata."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container=container_name, blob=blob_name)
        
        properties = blob_client.get_blob_properties()
        
        return {
            'success': True,
            'properties': {
                'name': blob_name,
                'container': container_name,
                'size': properties.size,
                'last_modified': properties.last_modified.isoformat(),
                'etag': properties.etag,
                'content_type': properties.content_settings.content_type if properties.content_settings else None,
                'content_encoding': properties.content_settings.content_encoding if properties.content_settings else None,
                'metadata': properties.metadata,
                'creation_time': properties.creation_time.isoformat() if properties.creation_time else None,
                'blob_type': properties.blob_type,
                'lease_state': properties.lease.state if properties.lease else None,
                'url': blob_client.url
            }
        }
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Blob {blob_name} not found in container {container_name}")
    except Exception as e:
        logger.error(f"Error getting blob properties {blob_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/docs/structure")
async def get_docs_structure():
    """Get documentation structure from Azure Blob Storage."""
    try:
        client = get_blob_service_client()
        
        # Check if documentation container exists
        docs_container = "documentation"
        try:
            container_client = client.get_container_client(docs_container)
            container_client.get_container_properties()  # Test if exists
        except ResourceNotFoundError:
            # Create documentation container if it doesn't exist
            container_client = client.get_container_client(docs_container)
            container_client.create_container()
            
            return {
                'success': True,
                'structure': {},
                'stats': {
                    'total_files': 0,
                    'categories': 0,
                    'total_size': 0
                },
                'message': 'Documentation container created'
            }
        
        # Get all documentation blobs
        blobs = list(container_client.list_blobs())
        
        # Organize by category (folder structure)
        structure = {}
        stats = {
            'total_files': len(blobs),
            'categories': 0,
            'total_size': 0
        }
        
        for blob in blobs:
            # Extract category from blob name (assumes folder/file structure)
            parts = blob.name.split('/')
            category = parts[0] if len(parts) > 1 else 'General'
            filename = parts[-1]
            
            if category not in structure:
                structure[category] = []
                stats['categories'] += 1
            
            structure[category].append({
                'name': filename,
                'path': blob.name,
                'size': blob.size or 0,
                'modified': blob.last_modified.isoformat() if blob.last_modified else None
            })
            
            stats['total_size'] += blob.size or 0
        
        return {
            'success': True,
            'structure': structure,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"Error getting docs structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/docs/content")
async def get_doc_content(path: str = Query(...)):
    """Get content of a specific documentation file from blob storage."""
    try:
        client = get_blob_service_client()
        blob_client = client.get_blob_client(container="documentation", blob=path)
        
        # Download and return content
        blob_data = blob_client.download_blob()
        content = blob_data.readall().decode('utf-8')
        properties = blob_client.get_blob_properties()
        
        return {
            'success': True,
            'content': content,
            'path': path,
            'size': properties.size,
            'modified': properties.last_modified.isoformat(),
            'type': 'markdown' if path.endswith('.md') else 'text'
        }
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Error getting doc content for {path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/docs/search")
async def search_docs(q: str = Query(...)):
    """Search documentation content in blob storage."""
    try:
        client = get_blob_service_client()
        container_client = client.get_container_client("documentation")
        
        results = []
        search_term = q.lower()
        
        # Search through all documentation blobs
        for blob in container_client.list_blobs():
            if not blob.name.endswith(('.md', '.txt', '.py')):
                continue
                
            try:
                blob_client = client.get_blob_client(container="documentation", blob=blob.name)
                blob_data = blob_client.download_blob()
                content = blob_data.readall().decode('utf-8')
                
                # Search in content and filename
                if search_term in content.lower() or search_term in blob.name.lower():
                    # Find matching lines
                    matches = []
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if search_term in line.lower():
                            matches.append({
                                'line': i + 1,
                                'text': line.strip()[:100] + '...' if len(line.strip()) > 100 else line.strip()
                            })
                            if len(matches) >= 3:  # Limit matches per file
                                break
                    
                    results.append({
                        'path': blob.name,
                        'name': blob.name.split('/')[-1],
                        'matches': matches,
                        'match_count': content.lower().count(search_term)
                    })
                    
            except Exception:
                continue  # Skip files that can't be read
        
        # Sort by match count
        results.sort(key=lambda x: x['match_count'], reverse=True)
        
        return {
            'success': True,
            'results': results[:20],  # Limit to top 20 results
            'total': len(results),
            'search_term': q
        }
        
    except Exception as e:
        logger.error(f"Error searching docs: {e}")
        raise HTTPException(status_code=500, detail=str(e))