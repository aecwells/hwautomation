# Project Status and Roadmap

This document summarizes what’s implemented today and what’s planned next, without internal phase labels.

## ✅ Current Capabilities

- Hardware management
  - Redfish API operations (power control, system info, basic BIOS)
  - IPMI utilities for power and BMC access
- Firmware management
  - Repository-driven mapping, mock/initial update flows, prioritization
  - Web endpoints and progress updates for firmware actions
- BIOS configuration
  - Template- and rules-based configuration with device mappings
  - Preserve-list handling and configuration merge
- Orchestration
  - Workflow engine with sub-task reporting and cancellation
  - Server provisioning workflow with shared context
- Web and API
  - Flask app with REST endpoints and real-time updates via WebSocket
- Data and persistence
  - SQLite with migrations and helper utilities

## 🚧 In Progress / Near-term

- Strengthened Redfish/IPMI retry, timeouts, and error mapping
- Policy-driven firmware gating (min versions, allowlist/denylist)
- Operator-facing progress details and audit logs in the web UI
- Expanded unit tests for orchestration, MAAS, and migrations

## 🧭 Planned Enhancements

- Vendor plugin interface for firmware and BIOS tools
- OpenAPI spec and typed clients for the web API
- Observability: Prometheus metrics, structured JSON logs, tracing
- Postgres option for higher-concurrency deployments
- Security hardening: secret filtering, TLS verification, rate limits

## 📌 Notes

- See `docs/README.md` for topic-specific guides
- Examples under `examples/` and tests under `tests/` illustrate usage patterns
- Configuration lives in `configs/`; environment via `.env` or settings files
