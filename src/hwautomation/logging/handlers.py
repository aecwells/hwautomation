"""
Custom log handlers for HWAutomation.

This module provides specialized handlers for different logging scenarios:
- DatabaseHandler: Log to database for dashboard integration
- WebSocketHandler: Real-time log streaming to web clients
- MetricsHandler: Extract metrics from log data
- RotatingFileHandler: Enhanced file rotation with compression
"""

import gzip
import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import sqlite3


class DatabaseHandler(logging.Handler):
    """
    Custom handler that writes logs to SQLite database for dashboard integration.

    Features:
    - Efficient batch insertions
    - Automatic database creation
    - Log retention policies
    - Dashboard-optimized queries
    """

    def __init__(
        self, db_path: str, table_name: str = "logs", max_records: int = 10000
    ):
        super().__init__()
        self.db_path = Path(db_path)
        self.table_name = table_name
        self.max_records = max_records
        self.batch_size = 100
        self.pending_records: List[Dict[str, Any]] = []

        # Create database and table if needed
        self._init_database()

        # Setup periodic flush
        self._last_flush = time.time()
        self._flush_interval = 5.0  # seconds

    def _init_database(self):
        """Initialize database and create logs table."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS {} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    logger TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    correlation_id TEXT,
                    thread_id INTEGER,
                    process_id INTEGER,
                    filename TEXT,
                    line_number INTEGER,
                    function_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """.format(
                    self.table_name
                )
            )

            # Create index for faster queries
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_timestamp
                ON {self.table_name}(timestamp)
            """
            )
            conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS idx_{self.table_name}_level
                ON {self.table_name}(level)
            """
            )

    def emit(self, record: logging.LogRecord):
        """Add log record to pending batch."""
        try:
            # Extract component name from logger
            component = (
                record.name.split(".")[-1] if "." in record.name else record.name
            )

            log_entry = {
                "timestamp": self.format(record),
                "level": record.levelname,
                "logger": record.name,
                "component": component,
                "message": record.getMessage(),
                "correlation_id": getattr(record, "correlation_id", None),
                "thread_id": record.thread,
                "process_id": record.process,
                "filename": record.filename,
                "line_number": record.lineno,
                "function_name": record.funcName,
            }

            self.pending_records.append(log_entry)

            # Flush if batch is full or time interval exceeded
            current_time = time.time()
            if (
                len(self.pending_records) >= self.batch_size
                or current_time - self._last_flush >= self._flush_interval
            ):
                self._flush_records()

        except Exception:
            self.handleError(record)

    def _flush_records(self):
        """Flush pending records to database."""
        if not self.pending_records:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert records
                placeholders = ", ".join(["?" * 12])
                conn.executemany(
                    f"""
                    INSERT INTO {self.table_name}
                    (timestamp, level, logger, component, message, correlation_id,
                     thread_id, process_id, filename, line_number, function_name)
                    VALUES ({placeholders})
                """,
                    [
                        (
                            r["timestamp"],
                            r["level"],
                            r["logger"],
                            r["component"],
                            r["message"],
                            r["correlation_id"],
                            r["thread_id"],
                            r["process_id"],
                            r["filename"],
                            r["line_number"],
                            r["function_name"],
                        )
                        for r in self.pending_records
                    ],
                )

                # Cleanup old records if needed
                self._cleanup_old_records(conn)

            self.pending_records.clear()
            self._last_flush = time.time()

        except Exception as e:
            # If database write fails, fall back to stderr
            print(f"Database logging failed: {e}", file=sys.stderr)

    def _cleanup_old_records(self, conn: sqlite3.Connection):
        """Remove old records to maintain max_records limit."""
        cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
        count = cursor.fetchone()[0]

        if count > self.max_records:
            records_to_delete = count - self.max_records
            conn.execute(
                f"""
                DELETE FROM {self.table_name}
                WHERE id IN (
                    SELECT id FROM {self.table_name}
                    ORDER BY created_at ASC
                    LIMIT ?
                )
            """,
                (records_to_delete,),
            )

    def close(self):
        """Flush remaining records and close handler."""
        self._flush_records()
        super().close()


class WebSocketHandler(logging.Handler):
    """
    Handler that broadcasts log messages to WebSocket clients in real-time.

    Features:
    - Real-time log streaming to web dashboard
    - Client filtering by log level and component
    - Efficient message broadcasting
    - Connection management
    """

    def __init__(self, websocket_manager=None):
        super().__init__()
        self.websocket_manager = websocket_manager
        self.client_filters: Dict[str, Dict[str, Any]] = {}

    def set_websocket_manager(self, manager):
        """Set the WebSocket manager after initialization."""
        self.websocket_manager = manager

    def emit(self, record: logging.LogRecord):
        """Broadcast log record to connected WebSocket clients."""
        if not self.websocket_manager:
            return

        try:
            component = (
                record.name.split(".")[-1] if "." in record.name else record.name
            )

            log_data = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "component": component,
                "message": record.getMessage(),
                "correlation_id": getattr(record, "correlation_id", None),
            }

            # Broadcast to all connected clients
            self.websocket_manager.broadcast_log(log_data)

        except Exception:
            self.handleError(record)


class MetricsHandler(logging.Handler):
    """
    Handler that extracts metrics from log messages for monitoring.

    Features:
    - Error rate tracking
    - Performance metrics extraction
    - Component activity monitoring
    - Alert threshold detection
    """

    def __init__(self, metrics_callback: Optional[Callable] = None):
        super().__init__()
        self.metrics_callback = metrics_callback
        self.error_counts: Dict[str, int] = {}
        self.component_activity: Dict[str, int] = {}
        self.performance_metrics: Dict[str, List[float]] = {}

        # Reset metrics periodically
        self._last_reset = time.time()
        self._reset_interval = 300  # 5 minutes

    def emit(self, record: logging.LogRecord):
        """Extract metrics from log record."""
        try:
            component = (
                record.name.split(".")[-1] if "." in record.name else record.name
            )

            # Track component activity
            self.component_activity[component] = (
                self.component_activity.get(component, 0) + 1
            )

            # Track error rates
            if record.levelno >= logging.ERROR:
                self.error_counts[component] = self.error_counts.get(component, 0) + 1

            # Extract performance metrics from message
            message = record.getMessage()
            if "duration:" in message.lower():
                try:
                    # Extract duration values (simple regex would be better)
                    parts = message.split("duration:")
                    if len(parts) > 1:
                        duration_str = parts[1].split()[0]
                        duration = float(duration_str.rstrip("ms"))

                        if component not in self.performance_metrics:
                            self.performance_metrics[component] = []
                        self.performance_metrics[component].append(duration)
                except (ValueError, IndexError):
                    pass

            # Check if it's time to reset metrics
            current_time = time.time()
            if current_time - self._last_reset >= self._reset_interval:
                self._emit_metrics()
                self._reset_metrics()

        except Exception:
            self.handleError(record)

    def _emit_metrics(self):
        """Emit collected metrics."""
        if self.metrics_callback:
            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "error_counts": self.error_counts.copy(),
                "component_activity": self.component_activity.copy(),
                "performance_metrics": {
                    k: {
                        "count": len(v),
                        "avg": sum(v) / len(v) if v else 0,
                        "max": max(v) if v else 0,
                        "min": min(v) if v else 0,
                    }
                    for k, v in self.performance_metrics.items()
                },
            }
            self.metrics_callback(metrics_data)

    def _reset_metrics(self):
        """Reset metrics counters."""
        self.error_counts.clear()
        self.component_activity.clear()
        self.performance_metrics.clear()
        self._last_reset = time.time()


class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Enhanced rotating file handler with compression support.

    Features:
    - Automatic compression of rotated files
    - Configurable compression level
    - Better disk space utilization
    - Maintains file naming consistency
    """

    def __init__(
        self,
        filename,
        mode="a",
        maxBytes=0,
        backupCount=0,
        encoding=None,
        delay=False,
        compress_level=6,
    ):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.compress_level = compress_level

    def doRollover(self):
        """Do a rollover with compression."""
        if self.stream:
            self.stream.close()
            self.stream = None

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d.gz" % (self.baseFilename, i))
                dfn = self.rotation_filename("%s.%d.gz" % (self.baseFilename, i + 1))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)

            # Compress the current log file
            dfn = self.rotation_filename("%s.1.gz" % self.baseFilename)
            if os.path.exists(dfn):
                os.remove(dfn)

            # Compress the log file
            with open(self.baseFilename, "rb") as f_in:
                with gzip.open(dfn, "wb", compresslevel=self.compress_level) as f_out:
                    f_out.writelines(f_in)

            # Remove the original file
            os.remove(self.baseFilename)

        if not self.delay:
            self.stream = self._open()


class BufferedHandler(logging.Handler):
    """
    Buffered handler for high-performance logging scenarios.

    Features:
    - Configurable buffer size and flush intervals
    - Automatic flushing on buffer full or time elapsed
    - Reduced I/O operations for better performance
    - Emergency flush on critical errors
    """

    def __init__(
        self,
        target_handler: logging.Handler,
        buffer_size: int = 1000,
        flush_interval: float = 5.0,
    ):
        super().__init__()
        self.target_handler = target_handler
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer: List[logging.LogRecord] = []
        self._last_flush = time.time()

    def emit(self, record: logging.LogRecord):
        """Add record to buffer."""
        self.buffer.append(record)

        # Flush immediately on critical errors
        if record.levelno >= logging.CRITICAL:
            self.flush()
        # Flush if buffer is full or time interval exceeded
        elif (
            len(self.buffer) >= self.buffer_size
            or time.time() - self._last_flush >= self.flush_interval
        ):
            self.flush()

    def flush(self):
        """Flush buffered records to target handler."""
        if not self.buffer:
            return

        for record in self.buffer:
            self.target_handler.emit(record)

        self.buffer.clear()
        self._last_flush = time.time()

        # Flush target handler too
        if hasattr(self.target_handler, "flush"):
            self.target_handler.flush()

    def close(self):
        """Flush remaining records and close."""
        self.flush()
        super().close()
        if hasattr(self.target_handler, "close"):
            self.target_handler.close()
