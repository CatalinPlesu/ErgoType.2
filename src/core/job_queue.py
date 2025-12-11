"""
Distributed job queue abstraction supporting RabbitMQ with in-memory fallback.
Provides seamless operation whether RabbitMQ is available or not.
"""

import json
import queue
import threading
from typing import Optional, Dict, Any, Tuple
import time
import pika

class JobQueue:
    """
    Queue abstraction for distributed GA evaluation.
    
    Connection config (modify as needed):
    - host: RabbitMQ server IP
    - port: AMQP port (default 5672)
    - user/pass: Authentication
    """
    
    # RabbitMQ connection configuration - MODIFY THESE AS NEEDED
    RABBITMQ_CONFIG = {
        'host': '100.127.28.27',  # Change to your RabbitMQ server IP
        'port': 5672,
        'user': 'user',
        'pass': 'pass',
        'virtual_host': '/'
    }
    
    def __init__(self, use_rabbitmq=True):
        """
        Initialize queue system.
        
        Args:
            use_rabbitmq: Try to use RabbitMQ if True, otherwise use in-memory
        """
        self.use_rabbitmq = use_rabbitmq 
        self.connection = None
        self.channel = None
        
        # Queue names
        self.JOBS_QUEUE = 'ga_jobs'
        self.RESULTS_QUEUE = 'ga_results'
        self.CONFIG_QUEUE = 'ga_config'
        
        # In-memory fallback
        self._jobs_queue = queue.Queue()
        self._results_queue = queue.Queue()
        self._config_queue = queue.Queue()
        self._lock = threading.Lock()
        
        if self.use_rabbitmq:
            self._init_rabbitmq()
    
    def _init_rabbitmq(self):
        """Initialize RabbitMQ connection"""
        try:
            credentials = pika.PlainCredentials(
                self.RABBITMQ_CONFIG['user'],
                self.RABBITMQ_CONFIG['pass']
            )
            
            parameters = pika.ConnectionParameters(
                host=self.RABBITMQ_CONFIG['host'],
                port=self.RABBITMQ_CONFIG['port'],
                virtual_host=self.RABBITMQ_CONFIG['virtual_host'],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues (durable for persistence)
            self.channel.queue_declare(queue=self.JOBS_QUEUE, durable=True)
            self.channel.queue_declare(queue=self.RESULTS_QUEUE, durable=True)
            self.channel.queue_declare(queue=self.CONFIG_QUEUE, durable=False)  # Config is ephemeral
            
            # Set QoS - workers fetch one job at a time
            self.channel.basic_qos(prefetch_count=1)
            
            print(f"✅ Connected to RabbitMQ at {self.RABBITMQ_CONFIG['host']}:{self.RABBITMQ_CONFIG['port']}")
            
        except Exception as e:
            print(f"⚠️  Failed to connect to RabbitMQ: {e}")
            print("📦 Falling back to in-memory queue")
            self.use_rabbitmq = False
            self.connection = None
            self.channel = None
    
    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
                print("✅ RabbitMQ connection closed")
            except:
                pass
    
    def purge_all(self):
        """Purge all queues (called by master on startup)"""
        if self.use_rabbitmq and self.channel:
            try:
                self.channel.queue_purge(self.JOBS_QUEUE)
                self.channel.queue_purge(self.RESULTS_QUEUE)
                self.channel.queue_purge(self.CONFIG_QUEUE)
                print("🧹 Purged all RabbitMQ queues")
            except Exception as e:
                print(f"⚠️  Error purging queues: {e}")
        else:
            # Clear in-memory queues
            with self._lock:
                self._jobs_queue = queue.Queue()
                self._results_queue = queue.Queue()
                self._config_queue = queue.Queue()
            print("🧹 Purged all in-memory queues")
    
    def push_config(self, config: Dict[str, Any]):
        """Push configuration (master only)"""
        config_json = json.dumps(config)
        
        if self.use_rabbitmq and self.channel:
            try:
                # Clear old config first
                self.channel.queue_purge(self.CONFIG_QUEUE)
                # Push new config
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.CONFIG_QUEUE,
                    body=config_json,
                    properties=pika.BasicProperties(delivery_mode=1)  # Non-persistent
                )
            except Exception as e:
                print(f"⚠️  Error pushing config: {e}")
        else:
            with self._lock:
                # Clear and add new config
                self._config_queue = queue.Queue()
                self._config_queue.put(config_json)
    
    def get_config(self, timeout=5) -> Optional[Dict[str, Any]]:
        """Get configuration (worker fetches at start of each batch)"""
        if self.use_rabbitmq and self.channel:
            try:
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.CONFIG_QUEUE,
                    auto_ack=True
                )
                if body:
                    return json.loads(body)
                return None
            except Exception as e:
                print(f"⚠️  Error getting config: {e}")
                return None
        else:
            try:
                config_json = self._config_queue.get(timeout=timeout)
                # Put it back for other workers
                self._config_queue.put(config_json)
                return json.loads(config_json)
            except queue.Empty:
                return None
    
    def push_job(self, job: Dict[str, Any]):
        """Push a job to be evaluated"""
        job_json = json.dumps(job)
        
        if self.use_rabbitmq and self.channel:
            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.JOBS_QUEUE,
                    body=job_json,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Persistent
                    )
                )
            except Exception as e:
                print(f"⚠️  Error pushing job: {e}")
        else:
            self._jobs_queue.put(job_json)
    
    def pull_job(self, timeout=1) -> Tuple[Optional[Dict[str, Any]], Any]:
        """
        Pull a job to evaluate.
        Returns (job_data, delivery_tag) for RabbitMQ or (job_data, None) for in-memory.
        """
        if self.use_rabbitmq and self.channel:
            try:
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.JOBS_QUEUE,
                    auto_ack=False  # Manual ack for requeue on failure
                )
                if body:
                    job = json.loads(body)
                    return (job, method_frame.delivery_tag)
                return (None, None)
            except Exception as e:
                print(f"⚠️  Error pulling job: {e}")
                return (None, None)
        else:
            try:
                job_json = self._jobs_queue.get(timeout=timeout)
                return (json.loads(job_json), None)
            except queue.Empty:
                return (None, None)
    
    def ack_job(self, delivery_tag):
        """Acknowledge job completion (RabbitMQ only)"""
        if self.use_rabbitmq and self.channel and delivery_tag is not None:
            try:
                self.channel.basic_ack(delivery_tag=delivery_tag)
            except Exception as e:
                print(f"⚠️  Error acking job: {e}")
    
    def nack_job(self, delivery_tag, requeue=True):
        """Negative acknowledge - requeue job on failure (RabbitMQ only)"""
        if self.use_rabbitmq and self.channel and delivery_tag is not None:
            try:
                self.channel.basic_nack(delivery_tag=delivery_tag, requeue=requeue)
            except Exception as e:
                print(f"⚠️  Error nacking job: {e}")
    
    def push_result(self, result: Dict[str, Any]):
        """Push evaluation result"""
        result_json = json.dumps(result)
        
        if self.use_rabbitmq and self.channel:
            try:
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.RESULTS_QUEUE,
                    body=result_json,
                    properties=pika.BasicProperties(delivery_mode=2)
                )
            except Exception as e:
                print(f"⚠️  Error pushing result: {e}")
        else:
            self._results_queue.put(result_json)
    
    def pull_result(self, timeout=1) -> Optional[Dict[str, Any]]:
        """Pull evaluation result (master only)"""
        if self.use_rabbitmq and self.channel:
            try:
                method_frame, header_frame, body = self.channel.basic_get(
                    queue=self.RESULTS_QUEUE,
                    auto_ack=True
                )
                if body:
                    return json.loads(body)
                return None
            except Exception as e:
                print(f"⚠️  Error pulling result: {e}")
                return None
        else:
            try:
                result_json = self._results_queue.get(timeout=timeout)
                return json.loads(result_json)
            except queue.Empty:
                return None
    
    def get_jobs_queue_size(self) -> int:
        """Get approximate number of pending jobs"""
        if self.use_rabbitmq and self.channel:
            try:
                method = self.channel.queue_declare(
                    queue=self.JOBS_QUEUE,
                    durable=True,
                    passive=True  # Don't create, just query
                )
                return method.method.message_count
            except Exception as e:
                return 0
        else:
            return self._jobs_queue.qsize()
    
    def get_results_queue_size(self) -> int:
        """Get approximate number of pending results"""
        if self.use_rabbitmq and self.channel:
            try:
                method = self.channel.queue_declare(
                    queue=self.RESULTS_QUEUE,
                    durable=True,
                    passive=True
                )
                return method.method.message_count
            except Exception as e:
                return 0
        else:
            return self._results_queue.qsize()
