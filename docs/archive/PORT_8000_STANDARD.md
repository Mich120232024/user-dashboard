# PORT 8000 STANDARD - HARD RULE

**CREATED**: 2025-06-23  
**AUTHORITY**: HEAD_OF_ENGINEERING  
**STATUS**: ENFORCED

## 🚨 MANDATORY FRONTEND ACCESS STANDARD

**HARD RULE**: All frontend dashboard access MUST use port 8000

- **URL**: http://localhost:8000/professional-dashboard.html
- **NEVER USE**: Other ports (8080, 8001, 5000, etc.)
- **REASON**: Consistency, reliability, standardization

## BACKEND CORS CONFIGURATION

Backend configured to ONLY allow localhost:8000:
```python
allow_origins=["http://localhost:8000"]  # HARD RULE: Always use port 8000 for frontend
```

## API ENDPOINTS TESTED

✅ **File Viewer API**: All agent file paths working
- Absolute paths: `/Agent_Shells/AGENT_NAME/file.md`
- Relative paths: `file.md`
- Agent-relative: `AGENT_NAME/file.md`

## EVIDENCE OF COMPLIANCE

```bash
EVIDENCE: curl localhost:8420/api/v1/agents-async/agent/FULL_STACK_SOFTWARE_ENGINEER/file → success:true → API working
EVIDENCE: Frontend accessible at localhost:8000 → Server running → Standard enforced
EVIDENCE: CORS allows only localhost:8000 → Security configured → Access restricted
```

## ENFORCEMENT

This is now a **HARD RULE** - any deviation from port 8000 for frontend access is non-compliant.

—HEAD_OF_ENGINEERING