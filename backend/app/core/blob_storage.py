"""Azure Blob Storage integration for user documents."""

import logging
from typing import List, Optional, BinaryIO
from datetime import datetime
import os

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class BlobStorageManager:
    """Manages Azure Blob Storage operations for user documents."""
    
    def __init__(self, connection_string: str, container_name: str = "user-documents"):
        """Initialize Blob Storage connection."""
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self._ensure_container_exists()
    
    def _ensure_container_exists(self):
        """Create container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.create_container(self.container_name)
            logger.info(f"Created container: {self.container_name}")
        except ResourceExistsError:
            logger.info(f"Container already exists: {self.container_name}")
    
    def upload_document(self, file_path: str, file_data: BinaryIO, user_id: str, 
                       metadata: Optional[dict] = None) -> dict:
        """Upload a document to blob storage."""
        # Organize by user and date
        timestamp = datetime.utcnow()
        blob_path = f"{user_id}/{timestamp.year}/{timestamp.month:02d}/{os.path.basename(file_path)}"
        
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name, 
            blob=blob_path
        )
        
        # Add metadata
        if metadata is None:
            metadata = {}
        metadata.update({
            "user_id": user_id,
            "upload_time": timestamp.isoformat(),
            "original_name": os.path.basename(file_path)
        })
        
        # Upload
        blob_client.upload_blob(file_data, metadata=metadata, overwrite=True)
        
        return {
            "blob_path": blob_path,
            "url": blob_client.url,
            "metadata": metadata
        }
    
    def list_user_documents(self, user_id: str) -> List[dict]:
        """List all documents for a user."""
        container_client = self.blob_service_client.get_container_client(self.container_name)
        prefix = f"{user_id}/"
        
        documents = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            documents.append({
                "name": blob.name,
                "size": blob.size,
                "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
                "metadata": blob.metadata,
                "url": f"https://{self.blob_service_client.account_name}.blob.core.windows.net/{self.container_name}/{blob.name}"
            })
        
        return documents
    
    def get_document(self, blob_path: str) -> bytes:
        """Download a document from blob storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        
        try:
            return blob_client.download_blob().readall()
        except ResourceNotFoundError:
            raise FileNotFoundError(f"Document not found: {blob_path}")
    
    def delete_document(self, blob_path: str) -> bool:
        """Delete a document from blob storage."""
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        
        try:
            blob_client.delete_blob()
            return True
        except ResourceNotFoundError:
            return False
    
    def organize_documents(self, user_id: str, organization_rules: dict) -> dict:
        """Reorganize user documents based on rules."""
        # This can be expanded based on your needs
        # For now, it returns the current structure
        documents = self.list_user_documents(user_id)
        
        organized = {
            "by_year": {},
            "by_type": {},
            "total_size": 0,
            "document_count": len(documents)
        }
        
        for doc in documents:
            # Extract year from path
            path_parts = doc["name"].split("/")
            if len(path_parts) > 2:
                year = path_parts[1]
                if year not in organized["by_year"]:
                    organized["by_year"][year] = []
                organized["by_year"][year].append(doc)
            
            # Organize by file type
            ext = os.path.splitext(doc["name"])[1].lower()
            if ext not in organized["by_type"]:
                organized["by_type"][ext] = []
            organized["by_type"][ext].append(doc)
            
            organized["total_size"] += doc["size"] or 0
        
        return organized