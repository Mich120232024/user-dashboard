# Architecture Tab Documentation

## Overview
The Architecture tab (formerly Research Viz) provides an interactive HTML viewer for system architecture diagrams and technical documentation. It allows users to view HTML-based architecture diagrams with full-screen capabilities and organized categorization.

## Features

### 1. HTML Content Viewer
- **Sandboxed iframe** for secure HTML rendering
- Full support for interactive HTML diagrams
- Responsive layout that adapts to content size

### 2. Expandable Categories
- Documents organized by category:
  - System Architecture
  - Database Design
  - Frontend Components
  - Azure Infrastructure
  - Process Workflows
  - Agent & Team Systems
  - Project Architecture
  - Communication Protocols
  - Operations & Maintenance

### 3. Full-Screen Mode
- Toggle full-screen view for detailed diagram examination
- ESC key support for exiting full-screen
- Maintains aspect ratio and responsiveness

### 4. Smart Title Generation
- Converts file names to human-readable titles
- Examples:
  - `agent_initialization_lifecycle_architecture.html` → "Agent Initialization Life Cycle Architecture"
  - `database_schema_design.html` → "Database Schema Design"
  - `system_overview_diagram.html` → "System Overview Diagram"

## Backend Implementation

### API Endpoints

#### GET `/api/v1/architecture/list`
Lists all available architecture HTML files from configured directories.

**Response:**
```json
{
  "files": [
    {
      "name": "system_architecture.html",
      "display_name": "System Architecture",
      "path": "/full/path/to/file.html",
      "category": "System Architecture",
      "size": "45.2 KB",
      "modified": 1656789012.345
    }
  ],
  "count": 25,
  "base_paths": [...]
}
```

#### GET `/api/v1/architecture/content`
Retrieves HTML content for display in the iframe.

**Parameters:**
- `path`: Full path to the HTML file

**Response:**
```json
{
  "content": "<html>...</html>",
  "path": "/path/to/file.html",
  "name": "file.html",
  "size": 46234
}
```

#### GET `/api/v1/architecture/raw`
Serves raw HTML file directly (for iframe src).

**Parameters:**
- `path`: Full path to the HTML file

### Configuration
Architecture files are searched in these directories:
```python
ARCHITECTURE_BASE_PATHS = [
    "/System Enforcement Workspace/documentation",
    "/Engineering Workspace/docs",
    "/Engineering Workspace/Projects/user-dashboard-clean/docs"
]
```

## Frontend Implementation

### UI Components

1. **Left Panel** (30% width)
   - Expandable category sections
   - Click to expand/collapse categories
   - Active item highlighting

2. **Right Panel** (70% width)
   - iframe for HTML content display
   - Full-screen toggle button
   - Loading states

### Styling
- Consistent with Documentation tab design
- Dark theme with blue accents
- Smooth transitions and hover effects

### JavaScript Functions

#### `loadArchitectureFiles()`
- Fetches list of available HTML files
- Organizes by category
- Updates UI with expandable sections

#### `selectArchitectureFile(path, name)`
- Loads selected HTML file into iframe
- Updates active state
- Handles error states

#### `toggleArchitectureFullscreen()`
- Toggles full-screen mode
- Updates button text
- Handles ESC key events

## Usage

1. **Navigate to Architecture Tab**
   - Click "Architecture" in the main navigation

2. **Browse Categories**
   - Click category headers to expand
   - View available diagrams in each category

3. **View Diagrams**
   - Click on any diagram name
   - Content loads in the right panel
   - Use full-screen for detailed viewing

4. **Full-Screen Mode**
   - Click "Full Screen" button
   - Press ESC or click "Exit Full Screen" to return

## File Naming Conventions

For best display results, name HTML files descriptively:
- Use underscores or hyphens as word separators
- Include category keywords (system, database, frontend, etc.)
- Avoid special characters
- Examples:
  - `system_architecture_overview.html`
  - `database-schema-design.html`
  - `agent_lifecycle_diagram.html`

## Security Considerations

- All HTML content is sandboxed in iframes
- Path validation ensures files are from allowed directories
- No JavaScript execution from loaded HTML files
- Content-Security-Policy headers recommended

## Future Enhancements

1. **Search Functionality**
   - Search across diagram names and descriptions
   - Filter by tags or categories

2. **Export Options**
   - Download diagrams as images
   - Print-friendly versions

3. **Version Control**
   - Track diagram versions
   - Show last modified information

4. **Collaboration Features**
   - Comments on diagrams
   - Share links to specific views

## Troubleshooting

### Common Issues

1. **Diagram Not Loading**
   - Check file exists in allowed directories
   - Verify HTML file is valid
   - Check browser console for errors

2. **Full-Screen Not Working**
   - Some browsers require user interaction
   - Check browser permissions
   - Try using F11 as alternative

3. **Categories Not Expanding**
   - Refresh the page
   - Check JavaScript console
   - Verify API endpoint is accessible

### Debug Mode
Enable debug logging in browser console:
```javascript
window.architectureDebug = true;
```

This will log all API calls and file loading operations.