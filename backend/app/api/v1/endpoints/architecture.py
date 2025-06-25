"""
Architecture Diagrams API Endpoints
Serves HTML architecture diagrams and documentation
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import os
import mimetypes
from typing import List, Optional

router = APIRouter()

# Define where architecture files are stored
ARCHITECTURE_BASE_PATHS = [
    "/Users/mikaeleage/Research & Analytics Services/System Enforcement Workspace/DOCS/documentation",
    "/Users/mikaeleage/Research & Analytics Services/System Enforcement Workspace/docs",
    "/Users/mikaeleage/Research & Analytics Services/Engineering Workspace/documentation",
    "/Users/mikaeleage/Research & Analytics Services/Engineering Workspace/Projects/user-dashboard-clean/docs"
]

def find_html_files() -> List[dict]:
    """Find all HTML files in architecture directories"""
    files = []
    
    for base_path in ARCHITECTURE_BASE_PATHS:
        base = Path(base_path)
        if not base.exists():
            continue
            
        # Find all HTML files recursively
        for html_file in base.rglob("*.html"):
            try:
                stats = html_file.stat()
                relative_path = str(html_file.relative_to(base))
                
                # Better categorization and title cleaning
                category = "General"
                
                # Clean up display name for human readability
                clean_name = html_file.stem
                
                # Replace separators with spaces
                clean_name = clean_name.replace('_', ' ').replace('-', ' ')
                
                # Remove common prefixes like numbers (01, 02, etc.)
                words = clean_name.split()
                words = [word for word in words if not word.isdigit()]
                
                # Handle common technical abbreviations and terms
                word_replacements = {
                    'db': 'Database',
                    'ui': 'UI',
                    'api': 'API',
                    'auth': 'Authentication',
                    'config': 'Configuration',
                    'admin': 'Administration',
                    'mgmt': 'Management',
                    'proc': 'Process',
                    'arch': 'Architecture',
                    'sys': 'System',
                    'dev': 'Development',
                    'prod': 'Production'
                }
                
                # Apply replacements and proper capitalization
                cleaned_words = []
                for word in words:
                    word_lower = word.lower()
                    if word_lower in word_replacements:
                        cleaned_words.append(word_replacements[word_lower])
                    else:
                        cleaned_words.append(word.title())
                
                display_name = ' '.join(cleaned_words)
                
                # Handle specific patterns for better readability
                display_name = display_name.replace('Lifecycle', 'Life Cycle')
                display_name = display_name.replace('Initialization', 'Initialization')  # Keep full word for clarity
                display_name = display_name.replace('Architecture', 'Architecture')  # Keep full word
                display_name = display_name.replace('Infrastructure', 'Infrastructure')  # Keep full word
                
                # Limit title length for better display
                if len(display_name) > 40:
                    words = display_name.split()
                    # Shorten common long words
                    shortened_words = []
                    for word in words:
                        if word == 'Architecture':
                            shortened_words.append('Arch')
                        elif word == 'Infrastructure':
                            shortened_words.append('Infra')
                        elif word == 'Initialization':
                            shortened_words.append('Init')
                        elif word == 'Management':
                            shortened_words.append('Mgmt')
                        else:
                            shortened_words.append(word)
                    display_name = ' '.join(shortened_words)
                
                # Final cleanup - remove extra spaces
                display_name = ' '.join(display_name.split())
                
                name_lower = html_file.name.lower()
                if "system" in name_lower or "architecture" in name_lower:
                    category = "System Architecture"
                elif "database" in name_lower or "db" in name_lower or "cosmos" in name_lower:
                    category = "Database Design"
                elif "frontend" in name_lower or "ui" in name_lower or "dashboard" in name_lower:
                    category = "Frontend Components"
                elif "azure" in name_lower or "cloud" in name_lower or "deployment" in name_lower:
                    category = "Azure Infrastructure"
                elif "workflow" in name_lower or "process" in name_lower or "guide" in name_lower:
                    category = "Process Workflows"
                elif "team" in name_lower or "agent" in name_lower or "org" in name_lower or "initialization" in name_lower or "lifecycle" in name_lower:
                    category = "Agent & Team Systems"
                elif "project" in name_lower or "container" in name_lower:
                    category = "Project Architecture"
                elif "message" in name_lower or "protocol" in name_lower:
                    category = "Communication Protocols"
                elif "maintenance" in name_lower or "session" in name_lower:
                    category = "Operations & Maintenance"
                
                files.append({
                    "name": html_file.name,
                    "display_name": display_name,
                    "path": str(html_file),
                    "relative_path": relative_path,
                    "category": category,
                    "size": f"{stats.st_size / 1024:.1f} KB",
                    "modified": stats.st_mtime,
                    "base_path": str(base)
                })
            except Exception as e:
                print(f"Error processing {html_file}: {e}")
                continue
    
    # Sort by modified time, newest first
    files.sort(key=lambda x: x["modified"], reverse=True)
    return files

@router.get("/list")
async def list_architecture_files():
    """List all available architecture HTML files"""
    try:
        files = find_html_files()
        return {
            "files": files,
            "count": len(files),
            "base_paths": ARCHITECTURE_BASE_PATHS
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list architecture files: {str(e)}")

@router.get("/content")
async def get_architecture_content(path: str = Query(..., description="Full path to the HTML file")):
    """Get HTML content of an architecture file"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Architecture file not found")
        
        if not file_path.suffix.lower() == '.html':
            raise HTTPException(status_code=400, detail="Only HTML files are supported")
        
        # Security check - ensure file is in allowed directories
        allowed = False
        for base_path in ARCHITECTURE_BASE_PATHS:
            try:
                file_path.relative_to(Path(base_path))
                allowed = True
                break
            except ValueError:
                continue
        
        if not allowed:
            raise HTTPException(status_code=403, detail="Access to this file is not allowed")
        
        # Read and return content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "content": content,
            "path": str(file_path),
            "name": file_path.name,
            "size": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read architecture file: {str(e)}")

@router.get("/raw")
async def get_architecture_raw(path: str = Query(..., description="Full path to the HTML file")):
    """Serve raw HTML file directly"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Architecture file not found")
        
        # Security check
        allowed = False
        for base_path in ARCHITECTURE_BASE_PATHS:
            try:
                file_path.relative_to(Path(base_path))
                allowed = True
                break
            except ValueError:
                continue
        
        if not allowed:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Read file content and return as HTMLResponse for iframe display
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return HTMLResponse(
            content=content,
            media_type="text/html"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve file: {str(e)}")

@router.get("/download")
async def download_architecture(path: str = Query(..., description="Full path to the HTML file")):
    """Download architecture file"""
    try:
        file_path = Path(path)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Security check
        allowed = False
        for base_path in ARCHITECTURE_BASE_PATHS:
            try:
                file_path.relative_to(Path(base_path))
                allowed = True
                break
            except ValueError:
                continue
        
        if not allowed:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return FileResponse(
            path=str(file_path),
            media_type="application/octet-stream",
            filename=file_path.name,
            headers={"Content-Disposition": f"attachment; filename={file_path.name}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.get("/health")
async def architecture_health():
    """Check architecture system health"""
    try:
        files = find_html_files()
        base_paths_status = {}
        
        for base_path in ARCHITECTURE_BASE_PATHS:
            base_paths_status[base_path] = Path(base_path).exists()
        
        return {
            "status": "healthy",
            "files_found": len(files),
            "base_paths": base_paths_status,
            "categories": list(set(f["category"] for f in files))
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }