"""
Log aggregation and monitoring utilities for HWAutomation.

This module provides advanced logging functionality:
- LogAggregator: Collect and analyze logs from multiple sources
- LogAnalyzer: Extract insights and patterns from log data
- AlertManager: Monitor logs for critical conditions
- MetricsCollector: Extract performance metrics from logs
"""

import json
import re
import statistics
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import sqlite3


class LogAggregator:
    """
    Aggregates logs from multiple sources for centralized analysis.

    Features:
    - Multi-source log collection
    - Real-time log streaming
    - Log correlation across components
    - Batch processing for large volumes
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.processors: List[Callable] = []
        self._init_database()

    def _init_database(self):
        """Initialize aggregation database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS aggregated_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL,
                    correlation_id TEXT,
                    metadata TEXT,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS log_sessions (
                    session_id TEXT PRIMARY KEY,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    correlation_id TEXT,
                    component TEXT,
                    status TEXT,
                    metadata TEXT
                )
            """
            )

            # Create indexes for faster queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON aggregated_logs(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_correlation ON aggregated_logs(correlation_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_component ON aggregated_logs(component)"
            )

    def add_source(self, name: str, source_type: str, config: Dict[str, Any]):
        """Add a log source."""
        self.sources[name] = {
            "type": source_type,
            "config": config,
            "last_processed": None,
            "total_processed": 0,
            "errors": 0,
        }

    def add_processor(self, processor: Callable):
        """Add a log processor function."""
        self.processors.append(processor)

    def collect_logs(
        self, source_name: str, start_time: Optional[datetime] = None
    ) -> List[Dict]:
        """Collect logs from a specific source."""
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")

        source = self.sources[source_name]
        logs = []

        try:
            if source["type"] == "file":
                logs = self._collect_from_file(source["config"], start_time)
            elif source["type"] == "database":
                logs = self._collect_from_database(source["config"], start_time)
            elif source["type"] == "api":
                logs = self._collect_from_api(source["config"], start_time)

            # Process logs through processors
            for processor in self.processors:
                logs = processor(logs)

            # Store in aggregation database
            self._store_logs(source_name, logs)

            # Update source stats
            source["last_processed"] = datetime.now()
            source["total_processed"] += len(logs)

        except Exception as e:
            source["errors"] += 1
            raise Exception(f"Failed to collect from {source_name}: {e}")

        return logs

    def _collect_from_file(
        self, config: Dict, start_time: Optional[datetime]
    ) -> List[Dict]:
        """Collect logs from file source."""
        file_path = Path(config["path"])
        if not file_path.exists():
            return []

        logs = []
        with open(file_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                log_entry = self._parse_log_line(line, config.get("format", "standard"))
                if log_entry and (
                    not start_time
                    or datetime.fromisoformat(log_entry["timestamp"]) >= start_time
                ):
                    logs.append(log_entry)

        return logs

    def _collect_from_database(
        self, config: Dict, start_time: Optional[datetime]
    ) -> List[Dict]:
        """Collect logs from database source."""
        db_path = config["db_path"]
        table = config.get("table", "logs")

        with sqlite3.connect(db_path) as conn:
            query = f"SELECT * FROM {table}"
            params = []

            if start_time:
                query += " WHERE timestamp >= ?"
                params.append(start_time.isoformat())

            query += " ORDER BY timestamp"

            cursor = conn.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            logs = []
            for row in cursor:
                log_entry = dict(zip(columns, row))
                logs.append(log_entry)

        return logs

    def _collect_from_api(
        self, config: Dict, start_time: Optional[datetime]
    ) -> List[Dict]:
        """Collect logs from API source."""
        # Placeholder for API collection
        # In real implementation, would make HTTP requests
        return []

    def _parse_log_line(self, line: str, format_type: str) -> Optional[Dict]:
        """Parse a log line based on format."""
        if format_type == "standard":
            # Parse standard format: "timestamp - component - level - message"
            parts = line.strip().split(" - ", 3)
            if len(parts) >= 4:
                return {
                    "timestamp": parts[0],
                    "component": parts[1],
                    "level": parts[2],
                    "message": parts[3],
                    "correlation_id": None,
                }
        elif format_type == "json":
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass

        return None

    def _store_logs(self, source: str, logs: List[Dict]):
        """Store logs in aggregation database."""
        with sqlite3.connect(self.db_path) as conn:
            for log in logs:
                conn.execute(
                    """
                    INSERT INTO aggregated_logs
                    (timestamp, level, source, component, message, correlation_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        log.get("timestamp"),
                        log.get("level"),
                        source,
                        log.get("component"),
                        log.get("message"),
                        log.get("correlation_id"),
                        json.dumps(
                            {
                                k: v
                                for k, v in log.items()
                                if k
                                not in [
                                    "timestamp",
                                    "level",
                                    "component",
                                    "message",
                                    "correlation_id",
                                ]
                            }
                        ),
                    ),
                )

    def get_correlated_logs(self, correlation_id: str) -> List[Dict]:
        """Get all logs for a specific correlation ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM aggregated_logs
                WHERE correlation_id = ?
                ORDER BY timestamp
            """,
                (correlation_id,),
            )

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor]


class LogAnalyzer:
    """
    Analyzes log data to extract insights and patterns.

    Features:
    - Error pattern detection
    - Performance trend analysis
    - Anomaly detection
    - Component health scoring
    """

    def __init__(self, aggregator: LogAggregator):
        self.aggregator = aggregator
        self.patterns: Dict[str, re.Pattern] = {}
        self.metrics_cache: Dict[str, Any] = {}
        self.cache_timeout = 300  # 5 minutes

    def add_pattern(self, name: str, pattern: str):
        """Add a pattern for analysis."""
        self.patterns[name] = re.compile(pattern, re.IGNORECASE)

    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns in recent logs."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        with sqlite3.connect(self.aggregator.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT level, component, message, COUNT(*) as count
                FROM aggregated_logs
                WHERE timestamp >= ? AND level IN ('ERROR', 'CRITICAL')
                GROUP BY level, component, message
                ORDER BY count DESC
            """,
                (start_time.isoformat(),),
            )

            error_patterns = []
            for row in cursor:
                level, component, message, count = row
                error_patterns.append(
                    {
                        "level": level,
                        "component": component,
                        "message": message,
                        "count": count,
                        "rate": count / hours,
                    }
                )

        return {
            "analysis_period": f"{hours} hours",
            "total_errors": sum(p["count"] for p in error_patterns),
            "patterns": error_patterns[:20],  # Top 20 patterns
            "components_affected": len(set(p["component"] for p in error_patterns)),
        }

    def analyze_performance_trends(
        self, component: str, hours: int = 24
    ) -> Dict[str, Any]:
        """Analyze performance trends for a component."""
        cache_key = f"perf_{component}_{hours}"

        # Check cache
        if (
            cache_key in self.metrics_cache
            and time.time() - self.metrics_cache[cache_key]["timestamp"]
            < self.cache_timeout
        ):
            return self.metrics_cache[cache_key]["data"]

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        with sqlite3.connect(self.aggregator.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT timestamp, message FROM aggregated_logs
                WHERE component = ? AND timestamp >= ?
                AND message LIKE '%duration%'
                ORDER BY timestamp
            """,
                (component, start_time.isoformat()),
            )

            durations = []
            timestamps = []

            for timestamp, message in cursor:
                # Extract duration from message
                duration = self._extract_duration(message)
                if duration:
                    durations.append(duration)
                    timestamps.append(datetime.fromisoformat(timestamp))

        if not durations:
            return {"error": "No performance data found"}

        analysis = {
            "component": component,
            "sample_count": len(durations),
            "avg_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "std_deviation": statistics.stdev(durations) if len(durations) > 1 else 0,
            "trend": self._calculate_trend(timestamps, durations),
        }

        # Cache the result
        self.metrics_cache[cache_key] = {"timestamp": time.time(), "data": analysis}

        return analysis

    def _extract_duration(self, message: str) -> Optional[float]:
        """Extract duration value from log message."""
        # Look for patterns like "duration: 1.23s" or "took 456ms"
        patterns = [
            r"duration:\s*([0-9.]+)s",
            r"duration:\s*([0-9.]+)ms",
            r"took\s+([0-9.]+)s",
            r"took\s+([0-9.]+)ms",
            r"elapsed:\s*([0-9.]+)s",
            r"elapsed:\s*([0-9.]+)ms",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                # Convert ms to seconds
                if "ms" in pattern:
                    value /= 1000
                return value

        return None

    def _calculate_trend(self, timestamps: List[datetime], values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "insufficient_data"

        # Simple linear regression
        x_values = [t.timestamp() for t in timestamps]
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        if denominator == 0:
            return "stable"

        slope = numerator / denominator

        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    def detect_anomalies(self, component: str, hours: int = 24) -> List[Dict]:
        """Detect anomalies in component behavior."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

        with sqlite3.connect(self.aggregator.db_path) as conn:
            # Get log volume by hour
            cursor = conn.execute(
                """
                SELECT
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    COUNT(*) as log_count,
                    SUM(CASE WHEN level = 'ERROR' THEN 1 ELSE 0 END) as error_count
                FROM aggregated_logs
                WHERE component = ? AND timestamp >= ?
                GROUP BY hour
                ORDER BY hour
            """,
                (component, start_time.isoformat()),
            )

            hourly_data = list(cursor)

        if len(hourly_data) < 3:
            return []

        log_counts = [row[1] for row in hourly_data]
        error_counts = [row[2] for row in hourly_data]

        # Calculate z-scores for anomaly detection
        log_mean = statistics.mean(log_counts)
        log_std = statistics.stdev(log_counts) if len(log_counts) > 1 else 0

        error_mean = statistics.mean(error_counts)
        error_std = statistics.stdev(error_counts) if len(error_counts) > 1 else 0

        anomalies = []

        for i, (hour, log_count, error_count) in enumerate(hourly_data):
            # Check for log volume anomalies
            if log_std > 0:
                log_zscore = abs(log_count - log_mean) / log_std
                if log_zscore > 2:  # More than 2 standard deviations
                    anomalies.append(
                        {
                            "type": "log_volume_anomaly",
                            "timestamp": hour,
                            "value": log_count,
                            "expected": log_mean,
                            "severity": "high" if log_zscore > 3 else "medium",
                        }
                    )

            # Check for error rate anomalies
            if error_std > 0:
                error_zscore = abs(error_count - error_mean) / error_std
                if error_zscore > 2:
                    anomalies.append(
                        {
                            "type": "error_rate_anomaly",
                            "timestamp": hour,
                            "value": error_count,
                            "expected": error_mean,
                            "severity": "high" if error_zscore > 3 else "medium",
                        }
                    )

        return anomalies


class AlertManager:
    """
    Monitors logs for critical conditions and triggers alerts.

    Features:
    - Real-time alert evaluation
    - Configurable alert rules
    - Alert escalation and suppression
    - Integration with notification systems
    """

    def __init__(self):
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.suppressions: Dict[str, float] = {}
        self.notification_handlers: List[Callable] = []

    def add_rule(
        self,
        name: str,
        condition: str,
        severity: str,
        suppression_time: int = 300,
        escalation_time: int = 900,
    ):
        """Add an alert rule."""
        self.rules[name] = {
            "condition": condition,
            "severity": severity,
            "suppression_time": suppression_time,
            "escalation_time": escalation_time,
            "last_triggered": None,
            "trigger_count": 0,
        }

    def add_notification_handler(self, handler: Callable):
        """Add a notification handler."""
        self.notification_handlers.append(handler)

    def evaluate_log(self, log_entry: Dict[str, Any]):
        """Evaluate a log entry against alert rules."""
        current_time = time.time()

        for rule_name, rule in self.rules.items():
            if self._evaluate_condition(log_entry, rule["condition"]):
                # Check if alert is suppressed
                if (
                    rule_name in self.suppressions
                    and current_time < self.suppressions[rule_name]
                ):
                    continue

                # Trigger alert
                self._trigger_alert(rule_name, rule, log_entry, current_time)

    def _evaluate_condition(self, log_entry: Dict[str, Any], condition: str) -> bool:
        """Evaluate alert condition."""
        # Simple condition evaluation (in practice, would use a more sophisticated engine)
        try:
            # Create safe evaluation context
            context = {
                "level": log_entry.get("level", ""),
                "component": log_entry.get("component", ""),
                "message": log_entry.get("message", ""),
                "timestamp": log_entry.get("timestamp", ""),
            }

            # Replace condition variables
            eval_condition = condition
            for key, value in context.items():
                eval_condition = eval_condition.replace(f"{{{key}}}", f'"{value}"')

            # Safe evaluation (limited operations)
            if any(op in eval_condition for op in ["import", "exec", "eval", "__"]):
                return False

            return eval(eval_condition)
        except:
            return False

    def _trigger_alert(
        self,
        rule_name: str,
        rule: Dict[str, Any],
        log_entry: Dict[str, Any],
        current_time: float,
    ):
        """Trigger an alert."""
        alert = {
            "rule_name": rule_name,
            "severity": rule["severity"],
            "timestamp": current_time,
            "log_entry": log_entry,
            "trigger_count": rule["trigger_count"] + 1,
        }

        # Update rule state
        rule["last_triggered"] = current_time
        rule["trigger_count"] += 1

        # Add to history
        self.alert_history.append(alert)

        # Set suppression
        self.suppressions[rule_name] = current_time + rule["suppression_time"]

        # Send notifications
        for handler in self.notification_handlers:
            try:
                handler(alert)
            except Exception:
                pass  # Don't let notification failures break alerting

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts."""
        cutoff_time = time.time() - (hours * 3600)
        return [
            alert for alert in self.alert_history if alert["timestamp"] >= cutoff_time
        ]
