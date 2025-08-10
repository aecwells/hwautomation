"""
Phase 4: Advanced Logging Infrastructure - Usage Examples

This file demonstrates the new modular logging capabilities introduced in Phase 4.
"""

import time
import uuid
from datetime import datetime

# Import both legacy and new modular logging
from hwautomation.logging import get_logger  # Legacy interface (backward compatible)
from hwautomation.logging import reconfigure_logging  # New modular interface
from hwautomation.logging import (
    get_logging_status,
    get_metrics_handler,
    with_correlation,
)
from hwautomation.logging.filters import ComponentFilter, RateLimitFilter

# Import modular components for advanced usage
from hwautomation.logging.formatters import DashboardFormatter, JSONFormatter
from hwautomation.logging.handlers import DatabaseHandler, MetricsHandler
from hwautomation.logging.monitoring import AlertManager, LogAggregator, LogAnalyzer


def example_basic_usage():
    """Example: Basic usage with legacy interface (backward compatible)."""
    print("=== Basic Usage (Legacy Interface) ===")

    # This works exactly as before (Phase 1-3 compatibility)
    logger = get_logger(__name__)
    logger.info("This works with the existing logging system")
    logger.warning("No changes needed to existing code")


def example_modular_profiles():
    """Example: Using new logging profiles."""
    print("=== Modular Logging Profiles ===")

    # Development profile (maximum visibility)
    reconfigure_logging("development")
    logger = get_logger(__name__)
    logger.debug("Development: Full debugging enabled")
    logger.info("Development: Includes database logging and WebSocket streaming")

    # Production profile (performance optimized)
    reconfigure_logging("production")
    logger = get_logger(__name__)
    logger.warning("Production: Only warnings and errors")
    logger.error("Production: Compressed files, rate limiting, metrics")

    # Custom profile with overrides
    reconfigure_logging(
        "staging", level=20, features={"rate_limiting": False}  # INFO level
    )
    logger = get_logger(__name__)
    logger.info("Staging: Custom configuration with overrides")


def example_correlation_tracking():
    """Example: Enhanced correlation tracking."""
    print("=== Correlation Tracking ===")

    # Set up development profile for visibility
    reconfigure_logging("development")
    logger = get_logger(__name__)

    # Example 1: Manual correlation ID
    request_id = str(uuid.uuid4())[:8]
    logger = get_logger(__name__, correlation_id=request_id)
    logger.info("Processing user request")
    logger.info("Validating input data")
    logger.info("Request completed successfully")

    # Example 2: Context manager (preferred)
    with with_correlation(str(uuid.uuid4())[:8]):
        logger = get_logger(__name__)
        logger.info("Starting workflow operation")

        # Simulate nested operations
        def nested_operation():
            nested_logger = get_logger(f"{__name__}.nested")
            nested_logger.info("Nested operation - same correlation ID")

        nested_operation()
        logger.info("Workflow operation completed")


def example_component_filtering():
    """Example: Component-based filtering."""
    print("=== Component Filtering ===")

    # Create custom profile with component filtering
    reconfigure_logging(
        "development", filters=["correlation", "component"], level=10
    )  # DEBUG level

    # These will be logged (included components)
    main_logger = get_logger("hwautomation.main")
    main_logger.debug("Main application debug message")

    hardware_logger = get_logger("hwautomation.hardware.discovery")
    hardware_logger.info("Hardware discovery operation")

    # Simulate noisy component (would be filtered in production)
    noisy_logger = get_logger("urllib3.connectionpool")
    noisy_logger.debug("This would be filtered out in production")


def example_performance_logging():
    """Example: Performance tracking and metrics."""
    print("=== Performance Logging and Metrics ===")

    # Configure with metrics collection
    reconfigure_logging(
        "staging",
        handlers=["console", "file", "metrics"],
        features={"metrics_collection": True},
    )

    logger = get_logger(__name__)

    # Simulate operations with performance logging
    operations = ["database_query", "api_call", "file_processing"]

    for operation in operations:
        start_time = time.time()

        logger.info(f"Starting {operation}")

        # Simulate work
        time.sleep(0.1)

        duration = time.time() - start_time
        logger.info(f"Completed {operation} - duration: {duration:.3f}s")

        # Log errors occasionally
        if operation == "api_call":
            logger.error(f"Failed {operation} - timeout occurred")

    # Get metrics handler to check collected data
    metrics_handler = get_metrics_handler()
    if metrics_handler:
        print(f"Error counts: {metrics_handler.error_counts}")
        print(f"Component activity: {metrics_handler.component_activity}")


def example_advanced_handlers():
    """Example: Using advanced handlers directly."""
    print("=== Advanced Handler Usage ===")

    # Create custom database handler
    db_handler = DatabaseHandler("logs/custom_app.db", max_records=5000)
    db_handler.setFormatter(JSONFormatter())

    # Create logger with custom handler
    custom_logger = get_logger("custom_app")
    custom_logger.addHandler(db_handler)

    # Log some data
    custom_logger.info("Custom database logging")
    custom_logger.warning("This goes to both standard logs and custom DB")

    # Cleanup
    db_handler.close()


def example_log_aggregation():
    """Example: Log aggregation and analysis."""
    print("=== Log Aggregation and Analysis ===")

    # Create log aggregator
    aggregator = LogAggregator("logs/aggregated.db")

    # Add log sources
    aggregator.add_source(
        "main_app", "file", {"path": "logs/hwautomation.log", "format": "standard"}
    )

    aggregator.add_source(
        "error_logs", "file", {"path": "logs/errors.log", "format": "standard"}
    )

    # Collect recent logs
    try:
        main_logs = aggregator.collect_logs("main_app")
        print(f"Collected {len(main_logs)} main application logs")

        error_logs = aggregator.collect_logs("error_logs")
        print(f"Collected {len(error_logs)} error logs")

        # Analyze logs
        analyzer = LogAnalyzer(aggregator)

        # Get error patterns
        error_analysis = analyzer.analyze_error_patterns(hours=1)
        print(f"Error analysis: {error_analysis.get('total_errors', 0)} errors found")

        # Detect anomalies
        anomalies = analyzer.detect_anomalies(__name__, hours=1)
        print(f"Detected {len(anomalies)} anomalies")

    except Exception as e:
        print(f"Log aggregation error: {e}")


def example_alerting():
    """Example: Log-based alerting."""
    print("=== Log-based Alerting ===")

    # Create alert manager
    alert_manager = AlertManager()

    # Add alert rules
    alert_manager.add_rule(
        "critical_errors",
        '{level} == "CRITICAL"',
        "high",
        suppression_time=60,  # 1 minute
    )

    alert_manager.add_rule(
        "hardware_failures",
        '{component} == "hardware" and {level} == "ERROR"',
        "medium",
        suppression_time=300,  # 5 minutes
    )

    # Add notification handler
    def email_notification(alert):
        print(
            f"ALERT: {alert['rule_name']} - {alert['severity']} - {alert['log_entry']['message']}"
        )

    alert_manager.add_notification_handler(email_notification)

    # Simulate log entries that trigger alerts
    test_logs = [
        {
            "level": "CRITICAL",
            "component": "database",
            "message": "Database connection lost",
        },
        {"level": "ERROR", "component": "hardware", "message": "Disk failure detected"},
        {"level": "INFO", "component": "web", "message": "Normal operation"},
    ]

    for log_entry in test_logs:
        alert_manager.evaluate_log(log_entry)

    # Check recent alerts
    recent_alerts = alert_manager.get_recent_alerts(hours=1)
    print(f"Generated {len(recent_alerts)} alerts")


def example_logging_status():
    """Example: Monitoring logging system status."""
    print("=== Logging System Status ===")

    status = get_logging_status()
    print("Current logging configuration:")
    for key, value in status.items():
        print(f"  {key}: {value}")


def main():
    """Run all examples."""
    print("Phase 4: Advanced Logging Infrastructure Examples")
    print("=" * 60)

    examples = [
        example_basic_usage,
        example_modular_profiles,
        example_correlation_tracking,
        example_component_filtering,
        example_performance_logging,
        example_advanced_handlers,
        example_log_aggregation,
        example_alerting,
        example_logging_status,
    ]

    for i, example in enumerate(examples, 1):
        print(
            f"\n{i}. {example.__name__.replace('example_', '').replace('_', ' ').title()}"
        )
        print("-" * 40)
        try:
            example()
        except Exception as e:
            print(f"Example failed: {e}")

        if i < len(examples):
            time.sleep(1)  # Brief pause between examples


if __name__ == "__main__":
    main()
