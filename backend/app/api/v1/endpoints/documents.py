"""Document management endpoints."""

import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
import io

from app.core.config import settings
from app.core.blob_storage import BlobStorageManager
from app.api.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize blob storage manager
# In production, this would use proper Azure connection string from settings
blob_manager = None

def get_blob_manager():
    """Get or create blob storage manager."""
    global blob_manager
    if blob_manager is None:
        # Use connection string from settings
        connection_string = getattr(settings, 'azure_storage_connection_string', None)
        if connection_string:
            blob_manager = BlobStorageManager(connection_string)
        else:
            logger.warning("Azure Storage connection string not configured")
    return blob_manager


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document to blob storage."""
    bm = get_blob_manager()
    if not bm:
        raise HTTPException(status_code=503, detail="Storage service not configured")
    
    try:
        # Read file content
        content = await file.read()
        file_stream = io.BytesIO(content)
        
        # Upload to blob storage
        result = bm.upload_document(
            file_path=file.filename,
            file_data=file_stream,
            user_id=str(current_user.id),
            metadata={
                "content_type": file.content_type,
                "size": len(content)
            }
        )
        
        return {
            "success": True,
            "document": result
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/list")
async def list_documents(
    current_user: User = Depends(get_current_user)
):
    """List all documents for the current user."""
    bm = get_blob_manager()
    if not bm:
        raise HTTPException(status_code=503, detail="Storage service not configured")
    
    try:
        documents = bm.list_user_documents(str(current_user.id))
        organized = bm.organize_documents(str(current_user.id), {})
        
        return {
            "documents": documents,
            "organization": organized
        }
    except Exception as e:
        logger.error(f"List error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.get("/download/{path:path}")
async def download_document(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """Download a document."""
    bm = get_blob_manager()
    if not bm:
        raise HTTPException(status_code=503, detail="Storage service not configured")
    
    # Verify user owns this document
    if not path.startswith(f"{current_user.id}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        content = bm.get_document(path)
        filename = path.split("/")[-1]
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail="Download failed")


@router.delete("/{path:path}")
async def delete_document(
    path: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document."""
    bm = get_blob_manager()
    if not bm:
        raise HTTPException(status_code=503, detail="Storage service not configured")
    
    # Verify user owns this document
    if not path.startswith(f"{current_user.id}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        success = bm.delete_document(path)
        if success:
            return {"success": True, "message": "Document deleted"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail="Delete failed")