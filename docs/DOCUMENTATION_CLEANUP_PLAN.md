# Documentation Cleanup Plan

## Files to Remove (Outdated/Historical)
These files contain outdated information or are historical summaries that are no longer relevant:

### Migration and Refactoring Summaries
- `REFACTORING_COMPLETE.md` - Historical refactoring summary
- `CLEANUP_SUMMARY.md` - Old cleanup summary  
- `TESTING_MODERNIZATION_SUMMARY.md` - Historical testing migration
- `TESTING_MIGRATION_SUMMARY.md` - Duplicate testing summary
- `CONFIGURATION_MIGRATION_SUMMARY.md` - Historical config migration
- `ENHANCEMENT_IMPLEMENTATION_SUMMARY.md` - Old enhancement summary
- `ENHANCEMENTS_SUMMARY.md` - Historical enhancements
- `ENHANCED_DASHBOARD_SUMMARY.md` - Old dashboard summary
- `GUI_SIMPLIFICATION_COMPLETE.md` - Historical GUI changes
- `GUI_SIMPLIFICATION_SUMMARY.md` - Duplicate GUI summary

### Outdated Docker Documentation
- `DOCKER_SETUP.md` - Contains PostgreSQL/Redis setup instructions

### Migration-Specific Documentation  
- `DATABASE_MIGRATION_006.md` - Specific migration documentation
- `CONVERSION_GUIDE.md` - Legacy conversion guide

## Files to Update
These files contain relevant information but need updates to reflect current architecture:

### Core Documentation
- `README.md` (main) - ✅ UPDATED
- `docs/README.md` - Update to reflect current doc structure
- `CONTAINER_ARCHITECTURE.md` - ✅ UPDATED
- `docs/PROJECT_ORGANIZATION.md` - Update project structure

### Keep As-Is (Still Relevant)
- `BIOS_CONFIGURATION.md` - Core functionality
- `DATABASE_MIGRATIONS.md` - Core system documentation
- `HARDWARE_DISCOVERY.md` - Core functionality
- `VENDOR_DISCOVERY.md` - Core functionality
- `ENHANCED_COMMISSIONING.md` - Core functionality
- `DEVICE_SELECTION_SUMMARY.md` - Core functionality
- `FLEXIBLE_WORKFLOW_SUMMARY.md` - Core functionality
- `ORCHESTRATION.md` - Core functionality
- `COMMISSIONING_PROGRESS.md` - Core functionality
- `CONTAINER_CLEANUP_SUMMARY.md` - ✅ Recent and relevant
- `SSH_TIMEOUT_FIX.md` - Relevant fix documentation
- `REAL_TIME_MONITORING_FIXED.md` - Relevant fix documentation

## Proposed Actions
1. Remove outdated historical files
2. Update core documentation files
3. Consolidate redundant information
4. Ensure all remaining docs reflect current SQLite-based, single-container architecture
