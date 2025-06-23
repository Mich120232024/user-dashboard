# Project Documentation Template

## 📋 Project Overview

**Project Name**: [Project Name]  
**Project Type**: [Active/Archive/Planned]  
**Owner**: [HEAD_OF_ENGINEERING/HEAD_OF_RESEARCH]  
**Created**: [Date]  
**Last Updated**: [Date]  

### Executive Summary
[Brief 2-3 sentence summary of the project purpose and value]

### Key Stakeholders
- **Business Owner**: [Name/Role]
- **Technical Lead**: [Name/Role]
- **Primary Users**: [User Groups]

## 🎯 Project Goals & Objectives

### Primary Goals
1. [Goal 1]
2. [Goal 2]
3. [Goal 3]

### Success Metrics
- [ ] [Metric 1 with target]
- [ ] [Metric 2 with target]
- [ ] [Metric 3 with target]

## 🏗️ Technical Architecture

### System Architecture
[High-level architecture description]

### Technology Stack
- **Frontend**: [Technologies]
- **Backend**: [Technologies]
- **Database**: [Technologies]
- **Infrastructure**: [Azure services]

### Key Components
1. **[Component 1]**
   - Purpose: [Description]
   - Technology: [Tech stack]
   - Dependencies: [List]

2. **[Component 2]**
   - Purpose: [Description]
   - Technology: [Tech stack]
   - Dependencies: [List]

## 📊 Data Model

### Primary Entities
- **[Entity 1]**: [Description]
- **[Entity 2]**: [Description]

### Database Schema
```sql
-- Example schema
CREATE TABLE [table_name] (
    id VARCHAR(255) PRIMARY KEY,
    -- additional fields
);
```

## 🔌 API Reference

### Endpoints
| Method | Endpoint | Description | Authentication |
|--------|----------|-------------|----------------|
| GET    | /api/v1/[resource] | [Description] | Required |
| POST   | /api/v1/[resource] | [Description] | Required |

### Example Requests
```bash
# Example API call
curl -X GET http://localhost:8001/api/v1/[resource] \
  -H "Authorization: Bearer [token]"
```

## 🚀 Deployment Guide

### Prerequisites
- [ ] Azure subscription
- [ ] Required permissions
- [ ] Environment variables configured

### Deployment Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Configuration
```yaml
# Example configuration
environment: production
azure:
  subscription: [subscription-id]
  resource_group: [resource-group]
```

## 🔧 Operations & Maintenance

### Monitoring
- **Metrics**: [What to monitor]
- **Alerts**: [Alert conditions]
- **Dashboards**: [Dashboard locations]

### Backup & Recovery
- **Backup Schedule**: [Frequency]
- **Recovery Procedure**: [Steps]

### Known Issues
1. **[Issue 1]**: [Description and workaround]
2. **[Issue 2]**: [Description and workaround]

## 📚 Additional Resources

### Documentation
- [Link to detailed technical documentation]
- [Link to user guide]
- [Link to API documentation]

### Related Projects
- [Related Project 1]
- [Related Project 2]

## 📝 Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| [Date] | 1.0.0 | Initial release | [Name] |

---
*This document follows the standard project documentation template. Last reviewed: [Date]*