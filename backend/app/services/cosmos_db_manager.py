#!/usr/bin/env python3
"""
Comprehensive Azure Cosmos DB operations manager for Research & Analytics Services
Provides all database operations for agents with proper error handling and logging
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CosmosDBManager:
    """Complete database operations manager for Research & Analytics Services"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize Cosmos DB manager with environment variables"""
        self.endpoint = os.getenv('COSMOS_ENDPOINT')
        self.key = os.getenv('COSMOS_KEY')
        self.database_name = os.getenv('COSMOS_DATABASE', 'research-analytics-db')
        self.container_name = os.getenv('COSMOS_CONTAINER', 'messages')
        
        if not self.endpoint or not self.key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in .env file")
        
        # Initialize client and connections
        self.client = CosmosClient(self.endpoint, self.key)
        self.database = self.client.get_database_client(self.database_name)
        self.container = self.database.get_container_client(self.container_name)
        
        # Setup logging
        self.logger = logger or self._setup_logger()
        
        self.logger.info(f"CosmosDBManager initialized - Database: {self.database_name}, Container: {self.container_name}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger for database operations"""
        logger = logging.getLogger('CosmosDBManager')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    # === MESSAGE OPERATIONS ===
    
    def store_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store a message in Cosmos DB with proper formatting"""
        try:
            # Ensure required fields
            if 'id' not in message_data:
                message_data['id'] = f"msg_{datetime.now().isoformat()}_{hash(str(message_data)) % 10000:04d}"
            
            if 'partitionKey' not in message_data:
                timestamp = message_data.get('timestamp', datetime.now().isoformat() + 'Z')
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    message_data['partitionKey'] = dt.strftime('%Y-%m')
                except:
                    message_data['partitionKey'] = datetime.now().strftime('%Y-%m')
            
            # Add metadata
            message_data['createdDate'] = datetime.now().isoformat() + 'Z'
            message_data['modifiedDate'] = datetime.now().isoformat() + 'Z'
            
            # Store in database
            result = self.container.create_item(message_data)
            self.logger.info(f"Message stored: {result['id']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store message: {str(e)}")
            raise
    
    def get_message(self, message_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific message by ID and partition key"""
        try:
            result = self.container.read_item(message_id, partition_key)
            self.logger.info(f"Message retrieved: {message_id}")
            return result
        except CosmosResourceNotFoundError:
            self.logger.warning(f"Message not found: {message_id}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to retrieve message {message_id}: {str(e)}")
            raise
    
    def update_message(self, message_id: str, partition_key: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing message"""
        try:
            # Get current message
            current = self.get_message(message_id, partition_key)
            if not current:
                raise ValueError(f"Message {message_id} not found")
            
            # Apply updates
            current.update(updates)
            current['modifiedDate'] = datetime.now().isoformat() + 'Z'
            
            # Save updated message
            result = self.container.replace_item(message_id, current)
            self.logger.info(f"Message updated: {message_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to update message {message_id}: {str(e)}")
            raise
    
    def delete_message(self, message_id: str, partition_key: str) -> bool:
        """Delete a message"""
        try:
            self.container.delete_item(message_id, partition_key)
            self.logger.info(f"Message deleted: {message_id}")
            return True
        except CosmosResourceNotFoundError:
            self.logger.warning(f"Message not found for deletion: {message_id}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete message {message_id}: {str(e)}")
            raise
    
    # === QUERY OPERATIONS ===
    
    def query_messages(self, query: str, parameters: Optional[List[Dict]] = None, 
                      cross_partition: bool = True) -> List[Dict[str, Any]]:
        """Execute a SQL query against messages"""
        try:
            if parameters:
                results = list(self.container.query_items(
                    query, 
                    parameters=parameters,
                    enable_cross_partition_query=cross_partition
                ))
            else:
                results = list(self.container.query_items(
                    query, 
                    enable_cross_partition_query=cross_partition
                ))
            
            self.logger.info(f"Query executed: {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise
    
    def get_messages_by_type(self, message_type: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages by type"""
        query = "SELECT * FROM messages WHERE messages.type = @type"
        if limit:
            query += f" ORDER BY messages.timestamp DESC OFFSET 0 LIMIT {limit}"
        
        parameters = [{"name": "@type", "value": message_type}]
        return self.query_messages(query, parameters)
    
    def get_messages_by_agent(self, agent_name: str, direction: str = "both", 
                             limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages from/to a specific agent using unified query pattern"""
        if direction == "from":
            query = "SELECT * FROM messages WHERE messages['from'] = @agent"
        elif direction == "to":
            # Use unified query pattern to handle both string and array recipients
            query = "SELECT * FROM messages WHERE (messages['to'] = @agent OR ARRAY_CONTAINS(messages['to'], @agent))"
        else:  # both
            # Use unified query pattern for complete coverage
            query = "SELECT * FROM messages WHERE messages['from'] = @agent OR (messages['to'] = @agent OR ARRAY_CONTAINS(messages['to'], @agent))"
        
        if limit:
            query += f" ORDER BY messages.timestamp DESC OFFSET 0 LIMIT {limit}"
        
        parameters = [{"name": "@agent", "value": agent_name}]
        return self.query_messages(query, parameters)
    
    def get_agent_inbox(self, agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent inbox messages for agent using unified query pattern"""
        return self.get_messages_by_agent(agent_name, direction="to", limit=limit)
    
    def get_messages_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get messages within date range"""
        query = """
        SELECT * FROM messages 
        WHERE messages.timestamp >= @start_date 
        AND messages.timestamp <= @end_date
        ORDER BY messages.timestamp DESC
        """
        parameters = [
            {"name": "@start_date", "value": start_date},
            {"name": "@end_date", "value": end_date}
        ]
        return self.query_messages(query, parameters)
    
    def search_messages(self, search_term: str, field: str = "content") -> List[Dict[str, Any]]:
        """Full-text search in messages"""
        query = f"SELECT * FROM messages WHERE CONTAINS(messages.{field}, @search_term)"
        parameters = [{"name": "@search_term", "value": search_term}]
        return self.query_messages(query, parameters)
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent messages"""
        query = f"SELECT * FROM messages ORDER BY messages.timestamp DESC OFFSET 0 LIMIT {limit}"
        return self.query_messages(query)
    
    def get_messages_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a conversation thread"""
        query = "SELECT * FROM messages WHERE messages.threadId = @thread_id ORDER BY messages.timestamp ASC"
        parameters = [{"name": "@thread_id", "value": thread_id}]
        return self.query_messages(query, parameters)
    
    def get_messages_requiring_response(self) -> List[Dict[str, Any]]:
        """Get messages that require a response"""
        query = "SELECT * FROM messages WHERE messages.requiresResponse = true ORDER BY messages.timestamp ASC"
        return self.query_messages(query)
    
    # === ANALYTICS AND REPORTING ===
    
    def get_message_statistics(self) -> Dict[str, Any]:
        """Get comprehensive message statistics"""
        stats = {}
        
        # Total count
        total_query = "SELECT VALUE COUNT(1) FROM messages"
        stats['total_messages'] = self.query_messages(total_query)[0]
        
        # Count by type - simplified approach
        try:
            type_query = "SELECT messages.type FROM messages"
            type_results = self.query_messages(type_query)
            type_counts = {}
            for item in type_results:
                msg_type = item.get('type', 'UNKNOWN')
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
            stats['by_type'] = type_counts
        except:
            stats['by_type'] = {}
        
        # Count by agent (from) - simplified approach
        try:
            agent_query = "SELECT messages['from'] as from_agent FROM messages"
            agent_results = self.query_messages(agent_query)
            agent_counts = {}
            for item in agent_results:
                agent = item.get('from_agent', 'UNKNOWN')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1
            stats['by_agent'] = agent_counts
        except:
            stats['by_agent'] = {}
        
        # Messages by month - simplified approach
        try:
            month_query = "SELECT messages.partitionKey FROM messages"
            month_results = self.query_messages(month_query)
            month_counts = {}
            for item in month_results:
                month = item.get('partitionKey', 'UNKNOWN')
                month_counts[month] = month_counts.get(month, 0) + 1
            stats['by_month'] = month_counts
        except:
            stats['by_month'] = {}
        
        # Priority distribution - simplified approach
        try:
            priority_query = "SELECT messages.priority FROM messages"
            priority_results = self.query_messages(priority_query)
            priority_counts = {}
            for item in priority_results:
                priority = item.get('priority', 'medium')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            stats['by_priority'] = priority_counts
        except:
            stats['by_priority'] = {}
        
        return stats
    
    def get_agent_activity_report(self, days: int = 7) -> Dict[str, Any]:
        """Get agent activity report for recent days"""
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat() + 'Z'
        
        # Simple approach: get all recent messages and count locally
        try:
            query = """
            SELECT messages['from'] as from_agent, messages['to'] as to_agent
            FROM messages 
            WHERE messages.timestamp >= @cutoff_date
            """
            parameters = [{"name": "@cutoff_date", "value": cutoff_date}]
            
            messages = self.query_messages(query, parameters)
            
            # Count communication pairs locally
            activity_counts = {}
            for msg in messages:
                from_agent = msg.get('from_agent', 'UNKNOWN')
                to_agent = msg.get('to_agent', 'UNKNOWN')
                pair_key = f"{from_agent} → {to_agent}"
                
                if pair_key not in activity_counts:
                    activity_counts[pair_key] = {
                        'from': from_agent,
                        'to': to_agent,
                        'message_count': 0
                    }
                activity_counts[pair_key]['message_count'] += 1
            
            # Sort by message count
            activity_list = sorted(
                activity_counts.values(),
                key=lambda x: x['message_count'],
                reverse=True
            )
            
            return {
                'period_days': days,
                'cutoff_date': cutoff_date,
                'activity': activity_list
            }
            
        except Exception as e:
            self.logger.error(f"Activity report failed: {str(e)}")
            return {
                'period_days': days,
                'cutoff_date': cutoff_date,
                'activity': [],
                'error': str(e)
            }
    
    # === MIGRATION OPERATIONS ===
    
    def migrate_from_json_files(self, inbox_path: str) -> Dict[str, int]:
        """Migrate messages from JSON files to Cosmos DB"""
        stats = {'processed': 0, 'succeeded': 0, 'failed': 0, 'errors': []}
        
        messages_dir = os.path.join(inbox_path, 'messages')
        if not os.path.exists(messages_dir):
            raise FileNotFoundError(f"Messages directory not found: {messages_dir}")
        
        self.logger.info(f"Starting migration from: {messages_dir}")
        
        for filename in sorted(os.listdir(messages_dir)):
            if not filename.endswith('.json'):
                continue
                
            file_path = os.path.join(messages_dir, filename)
            stats['processed'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    message_data = json.load(f)
                
                # Transform and store message
                transformed = self._transform_file_message(filename, message_data)
                self.store_message(transformed)
                stats['succeeded'] += 1
                
                if stats['processed'] % 50 == 0:
                    self.logger.info(f"Migration progress: {stats['processed']} processed, {stats['succeeded']} succeeded")
                
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Failed to migrate {filename}: {str(e)}"
                stats['errors'].append(error_msg)
                self.logger.error(error_msg)
        
        self.logger.info(f"Migration complete: {stats['succeeded']}/{stats['processed']} successful")
        return stats
    
    def _transform_file_message(self, filename: str, message_data: Dict) -> Dict:
        """Transform file-based message to Cosmos DB format"""
        import re
        
        # Extract original ID from filename
        id_match = re.match(r'(\d+)_', filename)
        original_id = id_match.group(1) if id_match else filename.split('_')[0]
        
        # Get timestamp
        timestamp = (
            message_data.get('timestamp') or 
            message_data.get('createdAt') or 
            datetime.now().isoformat() + 'Z'
        )
        
        if not timestamp.endswith('Z'):
            timestamp += 'Z'
        
        # Create partition key
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            partition_key = dt.strftime('%Y-%m')
        except:
            partition_key = datetime.now().strftime('%Y-%m')
        
        # Transform to standard format
        transformed = {
            'id': f"{timestamp}_{original_id}",
            'partitionKey': partition_key,
            'originalId': original_id,
            'timestamp': timestamp,
            'type': message_data.get('type', 'UNKNOWN'),
            'from': message_data.get('from', ''),
            'to': message_data.get('to', ''),
            'cc': message_data.get('cc', []),
            'subject': message_data.get('subject', ''),
            'content': message_data.get('content', message_data.get('body', '')),
            'priority': message_data.get('priority', 'medium'),
            'status': message_data.get('status', 'sent'),
            'requiresResponse': message_data.get('requires_response', message_data.get('requiresResponse', False)),
            'responseDeadline': message_data.get('response_deadline', message_data.get('responseDeadline')),
            'attachments': message_data.get('attachments', []),
            'tags': self._extract_tags(message_data),
            'threadId': self._create_thread_id(message_data),
            'sourceFile': filename
        }
        
        return transformed
    
    def _extract_tags(self, message_data: Dict) -> List[str]:
        """Extract searchable tags from message"""
        tags = []
        
        # Type-based tags
        msg_type = message_data.get('type', '').lower()
        if msg_type:
            tags.append(msg_type)
        
        # Priority tags
        priority = message_data.get('priority', '').lower()
        if priority:
            tags.append(f"priority-{priority}")
        
        # Content-based tags
        content_text = str(message_data.get('content', '')) + str(message_data.get('subject', ''))
        key_terms = [
            'governance', 'compliance', 'architecture', 'deployment', 'bug-fix',
            'azure', 'cosmos', 'database', 'migration', 'agent', 'framework'
        ]
        
        for term in key_terms:
            if term in content_text.lower():
                tags.append(term)
        
        return list(set(tags))
    
    def _create_thread_id(self, message_data: Dict) -> str:
        """Generate thread ID for conversation grouping"""
        subject = message_data.get('subject', '').lower()
        
        if 'constitutional' in subject or 'role review' in subject:
            return 'constitutional-roles-2025-06'
        elif 'synthesis' in subject:
            return 'governance-synthesis-2025-06'
        elif 'audit' in subject:
            return 'external-audit-2025-06'
        elif 'roundtable' in subject:
            return 'management-roundtable-2025-06'
        elif 'heartbeat' in subject:
            return 'system-heartbeat'
        else:
            from_agent = message_data.get('from', '').lower()
            to_agent = message_data.get('to', '').lower()
            return f"{from_agent}-{to_agent}"
    
    # === UTILITY OPERATIONS ===
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health and connectivity"""
        try:
            # Test basic connectivity
            total_query = "SELECT VALUE COUNT(1) FROM messages"
            total_count = self.query_messages(total_query)[0]
            
            # Test write operation
            test_doc = {
                'id': f"health_check_{datetime.now().isoformat()}",
                'partitionKey': datetime.now().strftime('%Y-%m'),
                'type': 'HEALTH_CHECK',
                'content': 'Database health check',
                'timestamp': datetime.now().isoformat() + 'Z'
            }
            
            created = self.store_message(test_doc)
            self.delete_message(created['id'], created['partitionKey'])
            
            return {
                'status': 'healthy',
                'total_messages': total_count,
                'timestamp': datetime.now().isoformat() + 'Z',
                'database': self.database_name,
                'container': self.container_name
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat() + 'Z'
            }
    
    def backup_to_json(self, output_path: str, partition_key: Optional[str] = None) -> int:
        """Backup messages to JSON files"""
        if partition_key:
            query = "SELECT * FROM messages WHERE messages.partitionKey = @partition_key"
            parameters = [{"name": "@partition_key", "value": partition_key}]
            messages = self.query_messages(query, parameters)
        else:
            messages = self.query_messages("SELECT * FROM messages")
        
        os.makedirs(output_path, exist_ok=True)
        
        for message in messages:
            filename = f"{message['id']}.json"
            filepath = os.path.join(output_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Backed up {len(messages)} messages to {output_path}")
        return len(messages)

# === AGENT HELPER FUNCTIONS ===

def get_db_manager() -> CosmosDBManager:
    """Get a configured database manager instance"""
    return CosmosDBManager()

def store_agent_message(from_agent: str, to_agent: str, message_type: str, 
                       subject: str, content: str, priority: str = "medium",
                       requires_response: bool = False) -> Dict[str, Any]:
    """Quick function for agents to store messages"""
    db = get_db_manager()
    
    message = {
        'type': message_type,
        'from': from_agent,
        'to': to_agent,
        'subject': subject,
        'content': content,
        'priority': priority,
        'requiresResponse': requires_response,
        'timestamp': datetime.now().isoformat() + 'Z'
    }
    
    return db.store_message(message)

def get_agent_inbox(agent_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent messages for an agent"""
    db = get_db_manager()
    return db.get_messages_by_agent(agent_name, direction="to", limit=limit)

def search_messages_for_agent(search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search messages for agents"""
    db = get_db_manager()
    results = db.search_messages(search_term)
    return results[:limit] if limit else results