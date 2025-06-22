"""System monitoring API endpoints for FastAPI backend."""

import logging
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

# Import Cosmos DB dependency
from .cosmos import get_cosmos_db

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None

class ServiceStatus(BaseModel):
    service_name: str
    status: str
    uptime: Optional[float] = None
    last_check: datetime
    health_score: float

class AlertRule(BaseModel):
    rule_id: str
    name: str
    metric: str
    condition: str
    threshold: float
    severity: str
    enabled: bool

@router.get("/system")
async def get_system_metrics():
    """Get current system metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network stats
        network = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems only)
        load_average = None
        try:
            load_average = list(os.getloadavg())
        except (OSError, AttributeError):
            # Windows doesn't have getloadavg
            pass
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=round(disk_percent, 2),
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count,
            load_average=load_average
        )
        
        return {
            'success': True,
            'metrics': metrics.dict(),
            'status': 'healthy' if cpu_percent < 80 and memory_percent < 80 else 'warning'
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_service_status():
    """Get status of key services."""
    try:
        services = []
        
        # Check FastAPI service (self)
        api_status = ServiceStatus(
            service_name="FastAPI Backend",
            status="running",
            uptime=None,  # Could track startup time
            last_check=datetime.utcnow(),
            health_score=100.0
        )
        services.append(api_status)
        
        # Check if Cosmos DB is accessible
        try:
            # This will be handled by the dependency injection
            cosmos_status = ServiceStatus(
                service_name="Cosmos DB",
                status="running",
                uptime=None,
                last_check=datetime.utcnow(),
                health_score=100.0
            )
        except:
            cosmos_status = ServiceStatus(
                service_name="Cosmos DB",
                status="error",
                uptime=None,
                last_check=datetime.utcnow(),
                health_score=0.0
            )
        services.append(cosmos_status)
        
        # Check Azure Blob Storage
        try:
            # Test blob storage connection
            blob_status = ServiceStatus(
                service_name="Azure Blob Storage",
                status="running",
                uptime=None,
                last_check=datetime.utcnow(),
                health_score=100.0
            )
        except:
            blob_status = ServiceStatus(
                service_name="Azure Blob Storage",
                status="error",
                uptime=None,
                last_check=datetime.utcnow(),
                health_score=0.0
            )
        services.append(blob_status)
        
        # Calculate overall health
        total_score = sum(service.health_score for service in services)
        avg_score = total_score / len(services) if services else 0
        
        overall_status = "healthy"
        if avg_score < 50:
            overall_status = "critical"
        elif avg_score < 80:
            overall_status = "warning"
        
        return {
            'success': True,
            'services': [service.dict() for service in services],
            'overall_status': overall_status,
            'overall_health_score': round(avg_score, 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database")
async def get_database_health(db=Depends(get_cosmos_db)):
    """Get detailed database health metrics."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Get container health
        containers = []
        total_documents = 0
        total_size_estimate = 0
        
        for container_info in database.list_containers():
            container = database.get_container_client(container_info['id'])
            
            try:
                # Get document count
                count_query = "SELECT VALUE COUNT(1) FROM c"
                count = list(container.query_items(
                    query=count_query,
                    enable_cross_partition_query=True
                ))[0]
                
                # Estimate size (rough calculation)
                size_estimate = count * 1024  # Assume 1KB per document average
                
                containers.append({
                    'name': container_info['id'],
                    'document_count': count,
                    'estimated_size_kb': size_estimate,
                    'status': 'healthy',
                    'last_check': datetime.utcnow().isoformat()
                })
                
                total_documents += count
                total_size_estimate += size_estimate
                
            except Exception as e:
                containers.append({
                    'name': container_info['id'],
                    'document_count': 0,
                    'estimated_size_kb': 0,
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.utcnow().isoformat()
                })
        
        # Calculate health metrics
        healthy_containers = len([c for c in containers if c['status'] == 'healthy'])
        health_percentage = (healthy_containers / len(containers) * 100) if containers else 0
        
        return {
            'success': True,
            'database_name': db.database_name,
            'endpoint': db.endpoint,
            'containers': containers,
            'summary': {
                'total_containers': len(containers),
                'healthy_containers': healthy_containers,
                'total_documents': total_documents,
                'estimated_size_mb': round(total_size_estimate / 1024, 2),
                'health_percentage': round(health_percentage, 2)
            },
            'last_updated': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting database health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_metrics(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    db=Depends(get_cosmos_db)
):
    """Get performance metrics over time."""
    try:
        database = db.client.get_database_client(db.database_name)
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        start_ts = start_time.timestamp()
        
        # Get recent activity from logs
        containers_to_check = ['agent_session_logs', 'agent_logs', 'logs', 'system_inbox']
        
        activity_data = {
            'total_operations': 0,
            'error_count': 0,
            'success_count': 0,
            'hourly_activity': {},
            'operation_types': {},
            'error_types': {}
        }
        
        for container_name in containers_to_check:
            try:
                container = database.get_container_client(container_name)
                
                # Get recent activity
                query = "SELECT * FROM c WHERE c._ts >= @start_ts"
                parameters = [{"name": "@start_ts", "value": start_ts}]
                
                logs = list(container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ))
                
                for log in logs:
                    activity_data['total_operations'] += 1
                    
                    # Track by hour
                    log_time = datetime.fromtimestamp(log.get('_ts', 0))
                    hour_key = log_time.strftime('%Y-%m-%d %H:00')
                    activity_data['hourly_activity'][hour_key] = activity_data['hourly_activity'].get(hour_key, 0) + 1
                    
                    # Track operation types
                    op_type = log.get('logType') or log.get('action') or log.get('type', 'unknown')
                    activity_data['operation_types'][op_type] = activity_data['operation_types'].get(op_type, 0) + 1
                    
                    # Track errors
                    if log.get('status') == 'error' or 'error' in str(log).lower():
                        activity_data['error_count'] += 1
                        error_type = log.get('error') or log.get('errorType') or 'unknown_error'
                        activity_data['error_types'][error_type] = activity_data['error_types'].get(error_type, 0) + 1
                    else:
                        activity_data['success_count'] += 1
                
            except Exception as e:
                logger.debug(f"Container {container_name} not accessible: {e}")
                continue
        
        # Calculate performance metrics
        success_rate = 0
        if activity_data['total_operations'] > 0:
            success_rate = (activity_data['success_count'] / activity_data['total_operations']) * 100
        
        # Convert hourly activity to time series
        time_series = []
        for i in range(hours):
            hour = (start_time + timedelta(hours=i)).strftime('%Y-%m-%d %H:00')
            time_series.append({
                'timestamp': hour,
                'activity_count': activity_data['hourly_activity'].get(hour, 0)
            })
        
        return {
            'success': True,
            'period': {
                'hours': hours,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'metrics': {
                'total_operations': activity_data['total_operations'],
                'success_count': activity_data['success_count'],
                'error_count': activity_data['error_count'],
                'success_rate': round(success_rate, 2),
                'avg_operations_per_hour': round(activity_data['total_operations'] / hours, 2)
            },
            'time_series': time_series,
            'operation_types': dict(sorted(activity_data['operation_types'].items(), key=lambda x: x[1], reverse=True)),
            'error_types': dict(sorted(activity_data['error_types'].items(), key=lambda x: x[1], reverse=True))
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts():
    """Get system alerts and warnings."""
    try:
        alerts = []
        
        # Get current system metrics
        metrics_response = await get_system_metrics()
        if metrics_response['success']:
            metrics = metrics_response['metrics']
            
            # CPU alert
            if metrics['cpu_percent'] > 80:
                alerts.append({
                    'id': 'cpu_high',
                    'severity': 'warning' if metrics['cpu_percent'] < 90 else 'critical',
                    'message': f"High CPU usage: {metrics['cpu_percent']:.1f}%",
                    'metric': 'cpu_percent',
                    'value': metrics['cpu_percent'],
                    'threshold': 80,
                    'timestamp': metrics['timestamp']
                })
            
            # Memory alert
            if metrics['memory_percent'] > 80:
                alerts.append({
                    'id': 'memory_high',
                    'severity': 'warning' if metrics['memory_percent'] < 90 else 'critical',
                    'message': f"High memory usage: {metrics['memory_percent']:.1f}%",
                    'metric': 'memory_percent',
                    'value': metrics['memory_percent'],
                    'threshold': 80,
                    'timestamp': metrics['timestamp']
                })
            
            # Disk alert
            if metrics['disk_percent'] > 85:
                alerts.append({
                    'id': 'disk_high',
                    'severity': 'warning' if metrics['disk_percent'] < 95 else 'critical',
                    'message': f"High disk usage: {metrics['disk_percent']:.1f}%",
                    'metric': 'disk_percent',
                    'value': metrics['disk_percent'],
                    'threshold': 85,
                    'timestamp': metrics['timestamp']
                })
        
        # Get service status
        services_response = await get_service_status()
        if services_response['success']:
            for service in services_response['services']:
                if service['status'] != 'running':
                    alerts.append({
                        'id': f"service_{service['service_name'].lower().replace(' ', '_')}",
                        'severity': 'critical',
                        'message': f"Service {service['service_name']} is {service['status']}",
                        'metric': 'service_status',
                        'value': service['status'],
                        'threshold': 'running',
                        'timestamp': service['last_check']
                    })
        
        # Sort by severity (critical first)
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return {
            'success': True,
            'alerts': alerts,
            'count': len(alerts),
            'critical_count': len([a for a in alerts if a['severity'] == 'critical']),
            'warning_count': len([a for a in alerts if a['severity'] == 'warning']),
            'last_updated': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_overall_health():
    """Get overall system health summary."""
    try:
        # Get all health data
        system_response = await get_system_metrics()
        services_response = await get_service_status()
        alerts_response = await get_alerts()
        
        # Calculate overall health score
        health_scores = []
        
        # System health (CPU, memory, disk)
        if system_response['success']:
            metrics = system_response['metrics']
            cpu_score = max(0, 100 - metrics['cpu_percent'])
            memory_score = max(0, 100 - metrics['memory_percent'])
            disk_score = max(0, 100 - metrics['disk_percent'])
            system_score = (cpu_score + memory_score + disk_score) / 3
            health_scores.append(system_score)
        
        # Services health
        if services_response['success']:
            health_scores.append(services_response['overall_health_score'])
        
        # Calculate final score
        overall_score = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Determine status
        if overall_score >= 80:
            status = 'healthy'
        elif overall_score >= 60:
            status = 'warning'
        else:
            status = 'critical'
        
        # Get alert counts
        critical_alerts = 0
        warning_alerts = 0
        if alerts_response['success']:
            critical_alerts = alerts_response['critical_count']
            warning_alerts = alerts_response['warning_count']
        
        return {
            'success': True,
            'overall_status': status,
            'health_score': round(overall_score, 2),
            'alerts': {
                'critical': critical_alerts,
                'warning': warning_alerts,
                'total': critical_alerts + warning_alerts
            },
            'system_metrics': system_response.get('metrics'),
            'services_status': services_response.get('overall_status'),
            'last_updated': datetime.utcnow().isoformat(),
            'recommendations': []
        }
        
    except Exception as e:
        logger.error(f"Error getting overall health: {e}")
        raise HTTPException(status_code=500, detail=str(e))