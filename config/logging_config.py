"""
Comprehensive logging configuration for the RepSplit system
"""
import logging
import logging.handlers
import os
import json
import time
import functools
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import sqlite3


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'performance_metrics'):
            log_entry['performance_metrics'] = record.performance_metrics
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class PerformanceMonitor:
    """Performance monitoring and timing utilities"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.metrics: Dict[str, float] = {}
    
    def time_function(self, func_name: str = None):
        """Decorator to time function execution"""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    
                    # Log performance metric
                    self.logger.info(
                        f"Function {func_name or func.__name__} completed",
                        extra={
                            'performance_metrics': {
                                'function_name': func_name or func.__name__,
                                'execution_time_ms': round(execution_time * 1000, 2),
                                'status': 'success'
                            }
                        }
                    )
                    
                    # Store metric
                    metric_key = f"{func_name or func.__name__}_execution_time"
                    self.metrics[metric_key] = execution_time
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Log error with performance metric
                    self.logger.error(
                        f"Function {func_name or func.__name__} failed",
                        extra={
                            'performance_metrics': {
                                'function_name': func_name or func.__name__,
                                'execution_time_ms': round(execution_time * 1000, 2),
                                'status': 'error',
                                'error_type': type(e).__name__
                            }
                        },
                        exc_info=True
                    )
                    
                    raise
            
            return wrapper
        return decorator
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        if not self.metrics:
            return {"message": "No performance metrics recorded"}
        
        summary = {
            "total_functions_timed": len(self.metrics),
            "average_execution_time_ms": round(
                sum(self.metrics.values()) * 1000 / len(self.metrics), 2
            ),
            "slowest_function": max(self.metrics.items(), key=lambda x: x[1]),
            "fastest_function": min(self.metrics.items(), key=lambda x: x[1]),
            "all_metrics": {k: round(v * 1000, 2) for k, v in self.metrics.items()}
        }
        
        return summary


class DatabaseMonitor:
    """Database performance and health monitoring"""
    
    def __init__(self, db_path: str, logger: logging.Logger):
        self.db_path = db_path
        self.logger = logger
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database health and performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get database size
            db_size = os.path.getsize(self.db_path)
            
            # Get table counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            table_counts = {}
            total_rows = 0
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                table_counts[table_name] = count
                total_rows += count
            
            # Check database performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM messages LIMIT 1")
            cursor.fetchone()
            query_time = time.time() - start_time
            
            # Check for stale data (last update time)
            cursor.execute("SELECT MAX(timestamp) FROM messages")
            last_message_time = cursor.fetchone()[0]
            
            conn.close()
            
            health_status = {
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "table_count": len(tables),
                "total_rows": total_rows,
                "table_breakdown": table_counts,
                "query_performance_ms": round(query_time * 1000, 2),
                "last_message_timestamp": last_message_time,
                "data_freshness_hours": round((time.time() - (last_message_time or 0)) / 3600, 2) if last_message_time else None,
                "status": "healthy" if query_time < 0.1 else "performance_concern"
            }
            
            self.logger.info("Database health check completed", extra={
                'context': {'database_health': health_status}
            })
            
            return health_status
            
        except Exception as e:
            self.logger.error("Database health check failed", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def log_database_operation(self, operation: str, table: str, rows_affected: int, duration_ms: float):
        """Log database operation performance"""
        self.logger.info(
            f"Database operation: {operation} on {table}",
            extra={
                'context': {
                    'database_operation': {
                        'operation': operation,
                        'table': table,
                        'rows_affected': rows_affected,
                        'duration_ms': duration_ms
                    }
                }
            }
        )


class DataFreshnessMonitor:
    """Monitor data freshness and alert on stale data"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.freshness_thresholds = {
            'messages': 24,  # hours
            'calendar_meetings': 48,  # hours
            'telegram_messages': 24,  # hours
            'stage_detections': 24,  # hours
        }
    
    def check_data_freshness(self, db_path: str) -> Dict[str, Any]:
        """Check freshness of all data sources"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            freshness_report = {}
            current_time = time.time()
            
            for data_type, threshold_hours in self.freshness_thresholds.items():
                try:
                    if data_type == 'messages':
                        cursor.execute("SELECT MAX(timestamp) FROM messages")
                    elif data_type == 'calendar_meetings':
                        cursor.execute("SELECT MAX(timestamp) FROM calendar_meetings")
                    elif data_type == 'telegram_messages':
                        cursor.execute("SELECT MAX(timestamp) FROM telegram_messages")
                    elif data_type == 'stage_detections':
                        cursor.execute("SELECT MAX(timestamp) FROM stage_detections")
                    
                    result = cursor.fetchone()
                    last_timestamp = result[0] if result and result[0] else None
                    
                    if last_timestamp:
                        hours_old = (current_time - last_timestamp) / 3600
                        is_fresh = hours_old <= threshold_hours
                        
                        freshness_report[data_type] = {
                            'last_update_hours_ago': round(hours_old, 2),
                            'threshold_hours': threshold_hours,
                            'is_fresh': is_fresh,
                            'status': 'fresh' if is_fresh else 'stale'
                        }
                        
                        if not is_fresh:
                            self.logger.warning(
                                f"Data source {data_type} is stale",
                                extra={
                                    'context': {
                                        'data_freshness_alert': {
                                            'data_type': data_type,
                                            'hours_old': hours_old,
                                            'threshold': threshold_hours
                                        }
                                    }
                                }
                            )
                    else:
                        freshness_report[data_type] = {
                            'last_update_hours_ago': None,
                            'threshold_hours': threshold_hours,
                            'is_fresh': False,
                            'status': 'no_data'
                        }
                        
                        self.logger.warning(
                            f"Data source {data_type} has no data",
                            extra={
                                'context': {
                                    'data_freshness_alert': {
                                        'data_type': data_type,
                                        'status': 'no_data'
                                    }
                                }
                            }
                        )
                        
                except Exception as e:
                    self.logger.error(
                        f"Error checking freshness for {data_type}",
                        extra={
                            'context': {
                                'data_freshness_error': {
                                    'data_type': data_type,
                                    'error': str(e)
                                }
                            }
                        }
                    )
                    freshness_report[data_type] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            conn.close()
            
            # Overall freshness status
            stale_sources = [k for k, v in freshness_report.items() 
                           if v.get('status') == 'stale' or v.get('status') == 'no_data']
            
            overall_status = 'healthy' if not stale_sources else 'degraded'
            if len(stale_sources) > len(freshness_report) // 2:
                overall_status = 'critical'
            
            freshness_report['overall_status'] = overall_status
            freshness_report['stale_sources'] = stale_sources
            
            self.logger.info(
                f"Data freshness check completed. Overall status: {overall_status}",
                extra={
                    'context': {
                        'data_freshness_summary': {
                            'overall_status': overall_status,
                            'stale_sources_count': len(stale_sources),
                            'total_sources': len(freshness_report) - 1  # Exclude overall_status
                        }
                    }
                }
            )
            
            return freshness_report
            
        except Exception as e:
            self.logger.error("Data freshness check failed", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/repsplit.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> tuple[logging.Logger, PerformanceMonitor, DatabaseMonitor, DataFreshnessMonitor]:
    """Set up comprehensive logging system"""
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create root logger
    logger = logging.getLogger('repsplit')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with structured formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = StructuredFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_file_size,
        backupCount=backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Create monitoring components
    performance_monitor = PerformanceMonitor(logger)
    database_monitor = DatabaseMonitor("data/slack/repsplit.db", logger)
    data_freshness_monitor = DataFreshnessMonitor(logger)
    
    logger.info("Logging system initialized", extra={
        'context': {
            'logging_setup': {
                'log_level': log_level,
                'log_file': str(log_file),
                'max_file_size_mb': max_file_size // (1024 * 1024),
                'backup_count': backup_count
            }
        }
    })
    
    return logger, performance_monitor, database_monitor, data_freshness_monitor


if __name__ == "__main__":
    # Test logging setup
    logger, perf_mon, db_mon, freshness_mon = setup_logging()
    
    # Test performance monitoring
    @perf_mon.time_function("test_function")
    def test_function():
        time.sleep(0.1)
        return "success"
    
    test_function()
    
    # Test database monitoring
    health = db_mon.check_database_health()
    print("Database Health:", json.dumps(health, indent=2))
    
    # Test data freshness
    freshness = freshness_mon.check_data_freshness("data/slack/repsplit.db")
    print("Data Freshness:", json.dumps(freshness, indent=2))
    
    # Performance summary
    summary = perf_mon.get_metrics_summary()
    print("Performance Summary:", json.dumps(summary, indent=2))
