# HWAutomation Configuration Guide

Complete configuration documentation for device types, BIOS templates, firmware settings, and system parameters.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Device Configuration](#device-configuration)
- [BIOS Templates](#bios-templates)
- [Firmware Settings](#firmware-settings)
- [Environment Configuration](#environment-configuration)
- [Network Configuration](#network-configuration)
- [Security Configuration](#security-configuration)
- [Advanced Configuration](#advanced-configuration)

## 🚀 Quick Start

### Basic Configuration Setup

1. **Environment Variables** (create `.env` file):
```bash
# MaaS Configuration
MAAS_URL=http://192.168.1.240:5240/MAAS
MAAS_CONSUMER_KEY=your-consumer-key
MAAS_TOKEN_KEY=your-token-key
MAAS_TOKEN_SECRET=your-token-secret

# Database Configuration
DATABASE_PATH=./hw_automation.db

# Web Interface
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/hwautomation.log
```

2. **Basic Device Configuration**:
```yaml
# configs/bios/device_mappings.yaml (excerpt)
device_types:
  a1.c5.large:
    vendor: HPE
    model: ProLiant RL300 Gen11
    architecture: x86_64
    cpu_count: 16
    memory_gb: 32
    network_interfaces: 2
```

3. **Quick BIOS Template**:
```yaml
# configs/bios/template_rules.yaml (excerpt)
templates:
  a1.c5.large:
    boot_mode: UEFI
    virtualization_technology: Enabled
    hyper_threading: Enabled
    power_profile: Balanced
```

## 🔧 Device Configuration

### Device Types and Mappings

Device configurations are defined in `configs/bios/device_mappings.yaml`:

```yaml
device_types:
  # Current Naming Scheme
  a1.c5.large:
    vendor: HPE
    model: ProLiant RL300 Gen11
    architecture: x86_64
    cpu_count: 16
    memory_gb: 32
    network_interfaces: 2
    storage_slots: 8
    pcie_slots: 3
    form_factor: 1U
    power_consumption_watts: 350
    bios_vendor: HPE
    bmc_type: iLO5
    redfish_support: true
    management_tools:
      - hponcfg
      - conrep
      - hpsum

  d1.c1.small:
    vendor: Dell
    model: PowerEdge R340
    architecture: x86_64
    cpu_count: 4
    memory_gb: 16
    network_interfaces: 2
    storage_slots: 4
    pcie_slots: 2
    form_factor: 1U
    power_consumption_watts: 250
    bios_vendor: Dell
    bmc_type: iDRAC9
    redfish_support: true
    management_tools:
      - racadm
      - syscfg

  d1.c2.medium:
    vendor: Dell
    model: PowerEdge R440
    architecture: x86_64
    cpu_count: 8
    memory_gb: 32
    network_interfaces: 4
    storage_slots: 8
    pcie_slots: 3
    form_factor: 1U
    power_consumption_watts: 400
    bios_vendor: Dell
    bmc_type: iDRAC9
    redfish_support: true
    management_tools:
      - racadm
      - syscfg

  # Legacy Naming Scheme (for backwards compatibility)
  s2_c2_small:
    vendor: Supermicro
    model: SYS-1029U-TR4
    architecture: x86_64
    cpu_count: 8
    memory_gb: 16
    bios_vendor: AMI
    bmc_type: BMC

# Vendor-specific configuration
vendor_settings:
  HPE:
    default_username: ADMIN
    default_password_env: HPE_DEFAULT_PASSWORD
    tools_path: /opt/hpe
    firmware_repository: https://downloads.hpe.com

  Dell:
    default_username: root
    default_password_env: DELL_DEFAULT_PASSWORD
    tools_path: /opt/dell
    firmware_repository: https://downloads.dell.com

  Supermicro:
    default_username: ADMIN
    default_password_env: SMC_DEFAULT_PASSWORD
    tools_path: /opt/supermicro
```

### Device Type Inheritance

You can define base configurations that other device types inherit from:

```yaml
# Base configurations
base_configs:
  hpe_base: &hpe_base
    vendor: HPE
    bios_vendor: HPE
    bmc_type: iLO5
    redfish_support: true
    management_tools:
      - hponcfg
      - conrep
      - hpsum

  dell_base: &dell_base
    vendor: Dell
    bios_vendor: Dell
    bmc_type: iDRAC9
    redfish_support: true
    management_tools:
      - racadm
      - syscfg

device_types:
  a1.c5.large:
    <<: *hpe_base
    model: ProLiant RL300 Gen11
    cpu_count: 16
    memory_gb: 32

  a1.c3.medium:
    <<: *hpe_base
    model: ProLiant RL300 Gen10
    cpu_count: 8
    memory_gb: 16
```

## ⚙️ BIOS Templates

### Template Rules Configuration

BIOS templates are defined in `configs/bios/template_rules.yaml`:

```yaml
templates:
  # HPE ProLiant configurations
  a1.c5.large:
    # Boot Configuration
    boot_mode: UEFI
    secure_boot: Enabled
    boot_order:
      - Network
      - Hard_Drive
      - USB

    # CPU Configuration
    virtualization_technology: Enabled
    hyper_threading: Enabled
    cpu_power_management: Maximum_Performance
    turbo_boost: Enabled

    # Memory Configuration
    memory_patrol_scrubbing: Enabled
    memory_refresh_rate: Auto
    numa_optimization: Enabled

    # Power Management
    power_profile: Maximum_Performance
    dynamic_power_capping: Disabled
    power_regulator: HP_Static_High_Performance

    # I/O Configuration
    sr_iov: Enabled
    vt_d: Enabled
    pci_slot_power_management: Disabled

    # Network Configuration
    pxe_boot_policy: Auto
    network_boot_retry: Enabled
    wake_on_lan: Enabled

    # Security
    tpm_module: Enabled
    tpm_operation: Clear
    asset_tag: ""

    # Advanced Settings
    post_f1_prompt: Disabled
    f11_boot_menu: Enabled
    fan_failure_policy: Allow_Boot
    temperature_monitoring: Enabled

  # Dell PowerEdge configurations
  d1.c1.small:
    # Boot Configuration
    boot_mode: UEFI
    secure_boot: Enabled
    boot_sequence:
      - NIC.Integrated.1-1-1
      - HardDisk.List.1-1
      - USB.SlotsOnly

    # Processor Configuration
    logical_processor: Enabled
    virtualization_technology: Enabled
    execute_disable: Enabled
    hardware_prefetcher: Enabled

    # Memory Configuration
    memory_operating_mode: Optimizer_Mode
    node_interleaving: Disabled
    memory_patrol_scrub: Standard

    # Integrated Devices
    sr_iov_global: Enabled
    os_watchdog_timer: Disabled
    embedded_sata: AHCI

    # Power Management
    system_profile: Performance_Optimized
    cpu_power_management: Maximum_Performance
    memory_frequency: Maximum_Performance

    # Miscellaneous
    f1_f2_prompt_on_error: Enabled
    ac_power_recovery: Last
    in_system_characterization: Enabled

  # Supermicro configurations
  s2_c2_small:
    # Basic Settings
    boot_mode: UEFI
    above_4g_decoding: Enabled

    # CPU Configuration
    hyper_threading: Enabled
    cpu_c_state: Enabled
    cpu_p_state: Enabled

    # Memory
    memory_frequency: Auto
    memory_voltage: Auto

    # Power
    power_technology: Custom
    energy_efficient_turbo: Enabled

    # I/O
    vt_d: Enabled
    sr_iov: Enabled

# Template inheritance and overrides
template_inheritance:
  base_performance: &base_performance
    power_profile: Maximum_Performance
    cpu_power_management: Maximum_Performance
    memory_frequency: Maximum_Performance

  base_efficiency: &base_efficiency
    power_profile: Balanced
    cpu_power_management: Balanced
    memory_frequency: Auto

# Apply base configurations
template_overrides:
  a1.c5.large:
    <<: *base_performance

  d1.c1.small:
    <<: *base_efficiency
```

### Advanced BIOS Templates

For complex configurations, you can use conditional settings:

```yaml
# Conditional templates based on workload
workload_templates:
  compute_optimized:
    base_template: performance_base
    overrides:
      hyper_threading: Enabled
      turbo_boost: Enabled
      power_profile: Maximum_Performance

  memory_optimized:
    base_template: balanced_base
    overrides:
      numa_optimization: Enabled
      memory_patrol_scrubbing: Enabled
      memory_refresh_rate: High

  io_optimized:
    base_template: balanced_base
    overrides:
      sr_iov: Enabled
      vt_d: Enabled
      pci_slot_power_management: Disabled

# Apply workload templates to device types
device_workload_mapping:
  a1.c5.large: compute_optimized
  a1.m5.xlarge: memory_optimized
  a1.i3.large: io_optimized
```

### BIOS Settings Preservation

Configure which settings to preserve during updates in `configs/bios/preserve_settings.yaml`:

```yaml
# Global preservation rules
global_preserve:
  - asset_tag
  - service_tag
  - system_password
  - setup_password
  - power_on_password

# Vendor-specific preservation
vendor_preserve:
  HPE:
    - ilo_ip_address
    - ilo_gateway
    - ilo_subnet_mask
    - ilo_dns_servers
    - server_name
    - server_fqdn

  Dell:
    - idrac_ip_address
    - idrac_gateway
    - idrac_subnet_mask
    - idrac_dns_servers
    - system_location

  Supermicro:
    - bmc_ip_address
    - bmc_gateway
    - bmc_netmask

# Device-specific preservation
device_preserve:
  a1.c5.large:
    - custom_boot_string
    - oem_string_1
    - oem_string_2

  d1.c1.small:
    - custom_asset_information
    - system_purpose

# Critical settings that should never be changed
critical_preserve:
  - serial_number
  - product_key
  - license_key
  - manufacturing_date
  - warranty_information
```

## 🔧 Firmware Settings

### Firmware Configuration

Firmware settings are managed in `configs/firmware/`:

```yaml
# configs/firmware/firmware_mappings.yaml
firmware_repositories:
  HPE:
    base_url: https://downloads.hpe.com
    spp_location: /spp/
    individual_components: /drivers/
    authentication_required: false

  Dell:
    base_url: https://downloads.dell.com
    dup_location: /dup/
    individual_components: /drivers/
    authentication_required: false

  Supermicro:
    base_url: https://www.supermicro.com
    firmware_location: /support/resources/downloadcenter/
    authentication_required: true

# Device firmware mappings
device_firmware:
  a1.c5.large:
    vendor: HPE
    model: ProLiant RL300 Gen11
    supported_components:
      bios:
        current_version_command: "hponcfg -r /tmp/biosversion.xml"
        update_method: hpsum
        file_pattern: "*.fwpkg"

      ilo:
        current_version_command: "hponcfg -r /tmp/iloversion.xml"
        update_method: hpsum
        file_pattern: "*.fwpkg"

      nic:
        current_version_command: "hponcfg -r /tmp/nicversion.xml"
        update_method: hpsum
        file_pattern: "*.fwpkg"

      storage:
        current_version_command: "hpssacli ctrl all show config detail"
        update_method: hpsum
        file_pattern: "*.fwpkg"

  d1.c1.small:
    vendor: Dell
    model: PowerEdge R340
    supported_components:
      bios:
        current_version_command: "racadm get BIOS.Setup.BiosVer"
        update_method: dup
        file_pattern: "*.exe"

      idrac:
        current_version_command: "racadm getversion"
        update_method: dup
        file_pattern: "*.exe"
```

### Firmware Update Policies

```yaml
# configs/firmware/update_policies.yaml
update_policies:
  production:
    auto_update: false
    update_window:
      start_time: "02:00"
      end_time: "06:00"
      timezone: "UTC"
      allowed_days: ["Saturday", "Sunday"]

    approval_required: true
    rollback_enabled: true
    max_concurrent_updates: 2

    component_priorities:
      critical: ["bios", "bmc"]
      important: ["nic", "storage"]
      optional: ["gpu", "fpga"]

  development:
    auto_update: true
    update_window:
      start_time: "00:00"
      end_time: "23:59"
      timezone: "UTC"
      allowed_days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

    approval_required: false
    rollback_enabled: true
    max_concurrent_updates: 10

  testing:
    auto_update: true
    approval_required: false
    rollback_enabled: false
    test_latest: true

# Component-specific update rules
component_rules:
  bios:
    pre_update_backup: true
    reboot_required: true
    estimated_duration_minutes: 15

  bmc:
    pre_update_backup: true
    reboot_required: false
    estimated_duration_minutes: 10

  nic:
    pre_update_backup: false
    reboot_required: true
    estimated_duration_minutes: 5
```

## 🌐 Environment Configuration

### Application Configuration

Main application configuration in `config.yaml`:

```yaml
# Application Settings
app:
  name: HWAutomation
  version: 1.0.0
  debug: false
  secret_key: your-secret-key-here

# Database Configuration
database:
  type: sqlite
  path: hw_automation.db
  migration_dir: src/hwautomation/database/migrations
  backup_enabled: true
  backup_interval_hours: 24

# Web Interface
web:
  host: 0.0.0.0
  port: 5000
  enable_cors: true
  session_timeout_minutes: 60
  max_upload_size_mb: 100

# API Settings
api:
  rate_limit: 100  # requests per minute
  pagination_default: 50
  pagination_max: 500
  timeout_seconds: 30

# Workflow Configuration
workflows:
  max_concurrent: 10
  default_timeout_minutes: 60
  retry_attempts: 3
  retry_delay_seconds: 30

# Hardware Management
hardware:
  discovery_timeout_seconds: 30
  bios_config_timeout_minutes: 15
  firmware_update_timeout_minutes: 45
  default_credentials:
    username: ADMIN
    password_env_var: DEFAULT_BMC_PASSWORD

# MaaS Integration
maas:
  timeout_seconds: 30
  retry_attempts: 3
  commission_timeout_minutes: 30
  deploy_timeout_minutes: 60

# Logging Configuration
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  max_file_size_mb: 10
  backup_count: 5

  loggers:
    hwautomation: INFO
    hwautomation.database: DEBUG
    hwautomation.hardware: INFO
    hwautomation.maas: INFO

# Security Settings
security:
  password_min_length: 8
  session_secure_cookie: true
  csrf_protection: true
  rate_limiting: true

# Notification Settings
notifications:
  enabled: true
  webhook_url: ""
  email_enabled: false
  slack_enabled: false
```

### Docker Configuration

Configure Docker deployment in `docker-compose.yml`:

```yaml
version: '3.8'

services:
  hwautomation-web:
    build:
      context: .
      dockerfile: docker/Dockerfile.web
    container_name: hwautomation-web
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_PATH=/app/data/hw_automation.db
      - MAAS_URL=${MAAS_URL}
      - MAAS_CONSUMER_KEY=${MAAS_CONSUMER_KEY}
      - MAAS_TOKEN_KEY=${MAAS_TOKEN_KEY}
      - MAAS_TOKEN_SECRET=${MAAS_TOKEN_SECRET}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./configs:/app/configs
      - ./firmware:/app/firmware
    networks:
      - hwautomation-network
    restart: unless-stopped

  hwautomation-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.cli
    container_name: hwautomation-worker
    environment:
      - DATABASE_PATH=/app/data/hw_automation.db
      - WORKER_MODE=true
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./configs:/app/configs
      - ./firmware:/app/firmware
    networks:
      - hwautomation-network
    restart: unless-stopped
    depends_on:
      - hwautomation-web

networks:
  hwautomation-network:
    driver: bridge
```

### Development Override

Create `docker-compose.override.yml` for development:

```yaml
version: '3.8'

services:
  hwautomation-web:
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=true
    volumes:
      - .:/app
    ports:
      - "5000:5000"
      - "5678:5678"  # Debug port

  hwautomation-worker:
    environment:
      - WORKER_DEBUG=true
    volumes:
      - .:/app
```

## 🔒 Network Configuration

### IPMI Network Settings

Configure IPMI network ranges and settings:

```yaml
# configs/network/ipmi_config.yaml
ipmi_networks:
  production:
    network: 192.168.100.0/24
    gateway: 192.168.100.1
    dns_servers:
      - 8.8.8.8
      - 8.8.4.4
    vlan_id: 100

  development:
    network: 192.168.200.0/24
    gateway: 192.168.200.1
    dns_servers:
      - 192.168.200.1
    vlan_id: 200

  testing:
    network: 10.0.1.0/24
    gateway: 10.0.1.1
    dns_servers:
      - 10.0.1.1

# IP allocation policies
ip_allocation:
  strategy: sequential  # sequential, random, reserved_pool
  exclude_ranges:
    - 192.168.100.1-192.168.100.10   # Reserved for infrastructure
    - 192.168.100.250-192.168.100.255 # Reserved for broadcast

  allocation_pools:
    servers: 192.168.100.100-192.168.100.199
    switches: 192.168.100.200-192.168.100.229
    storage: 192.168.100.230-192.168.100.249

# Network validation rules
validation:
  ping_test: true
  port_scan: [22, 23, 80, 443, 623]
  timeout_seconds: 5
  retry_attempts: 3
```

### Firewall Configuration

Configure firewall rules for secure communication:

```yaml
# configs/network/firewall_rules.yaml
firewall_rules:
  inbound:
    # Web interface
    - port: 5000
      protocol: tcp
      source: any
      description: "Web interface access"

    # SSH access
    - port: 22
      protocol: tcp
      source: management_network
      description: "SSH management access"

    # IPMI access
    - port: 623
      protocol: udp
      source: ipmi_network
      description: "IPMI communication"

  outbound:
    # MaaS API
    - port: 5240
      protocol: tcp
      destination: maas_server
      description: "MaaS API communication"

    # DNS
    - port: 53
      protocol: udp
      destination: any
      description: "DNS resolution"

    # NTP
    - port: 123
      protocol: udp
      destination: any
      description: "Time synchronization"

# Network zones
network_zones:
  management_network: 192.168.1.0/24
  ipmi_network: 192.168.100.0/24
  maas_server: 192.168.1.240
```

## 🔐 Security Configuration

### Authentication and Authorization

```yaml
# configs/security/auth_config.yaml
authentication:
  methods:
    - local
    - ldap
    - oauth

  local:
    enabled: true
    password_policy:
      min_length: 8
      require_uppercase: true
      require_lowercase: true
      require_numbers: true
      require_special: true
      max_age_days: 90

  ldap:
    enabled: false
    server: ldap://ldap.example.com
    base_dn: dc=example,dc=com
    user_dn: cn={username},ou=users,dc=example,dc=com

  oauth:
    enabled: false
    provider: google
    client_id: your-client-id
    client_secret_env: OAUTH_CLIENT_SECRET

authorization:
  roles:
    admin:
      permissions:
        - workflow:create
        - workflow:read
        - workflow:update
        - workflow:delete
        - server:manage
        - config:manage

    operator:
      permissions:
        - workflow:create
        - workflow:read
        - server:read

    viewer:
      permissions:
        - workflow:read
        - server:read

# API Security
api_security:
  rate_limiting:
    enabled: true
    requests_per_minute: 100

  cors:
    enabled: true
    allowed_origins:
      - http://localhost:3000
      - https://hwautomation.example.com

  csrf_protection:
    enabled: true
    secret_key_env: CSRF_SECRET_KEY
```

### Credential Management

```yaml
# configs/security/credentials.yaml
credential_stores:
  vault:
    enabled: false
    url: https://vault.example.com
    auth_method: token
    token_env: VAULT_TOKEN

  environment:
    enabled: true
    prefix: HWAUTOMATION_

  file:
    enabled: false
    path: /etc/hwautomation/secrets
    encrypted: true

# Default credentials by vendor
default_credentials:
  HPE:
    username: ADMIN
    password_env: HPE_DEFAULT_PASSWORD

  Dell:
    username: root
    password_env: DELL_DEFAULT_PASSWORD

  Supermicro:
    username: ADMIN
    password_env: SMC_DEFAULT_PASSWORD

# Credential rotation
rotation_policy:
  enabled: true
  interval_days: 30
  notification_days_before: 7
  auto_rotate: false
```

## ⚡ Advanced Configuration

### Performance Tuning

```yaml
# configs/advanced/performance.yaml
performance:
  database:
    connection_pool_size: 20
    connection_timeout_seconds: 30
    query_timeout_seconds: 60

  workflow_engine:
    max_concurrent_workflows: 10
    worker_threads: 4
    queue_size: 100

  web_interface:
    max_connections: 1000
    connection_timeout_seconds: 30
    static_file_caching: true
    gzip_compression: true

  hardware_operations:
    concurrent_discovery: 5
    concurrent_bios_config: 3
    concurrent_firmware_updates: 2
    operation_timeout_multiplier: 1.5

# Caching configuration
caching:
  enabled: true
  backend: redis
  redis:
    host: localhost
    port: 6379
    db: 0

  cache_policies:
    device_mappings:
      ttl_seconds: 3600
      refresh_on_access: true

    bios_templates:
      ttl_seconds: 1800
      refresh_on_access: true

    hardware_discovery:
      ttl_seconds: 300
      refresh_on_access: false
```

### Monitoring and Alerting

```yaml
# configs/advanced/monitoring.yaml
monitoring:
  metrics:
    enabled: true
    endpoint: /metrics
    format: prometheus

  health_checks:
    enabled: true
    endpoint: /health
    checks:
      - database
      - maas_connectivity
      - disk_space
      - memory_usage

  alerting:
    enabled: true
    webhook_url: https://alerts.example.com/webhook

    rules:
      workflow_failure:
        condition: workflow_status == "FAILED"
        severity: high

      disk_space:
        condition: disk_usage_percent > 85
        severity: medium

      high_error_rate:
        condition: error_rate_per_minute > 10
        severity: high

# Log aggregation
log_aggregation:
  enabled: false
  backend: elasticsearch
  elasticsearch:
    hosts:
      - elasticsearch.example.com:9200
    index: hwautomation-logs
```

### Backup and Recovery

```yaml
# configs/advanced/backup.yaml
backup:
  database:
    enabled: true
    schedule: "0 2 * * *"  # Daily at 2 AM
    retention_days: 30
    backup_location: /backup/database
    compression: gzip

  configuration:
    enabled: true
    schedule: "0 3 * * 0"  # Weekly on Sunday at 3 AM
    retention_weeks: 12
    backup_location: /backup/config

  logs:
    enabled: true
    schedule: "0 1 * * *"  # Daily at 1 AM
    retention_days: 7
    backup_location: /backup/logs
    compression: gzip

recovery:
  automated_recovery:
    enabled: true
    max_attempts: 3

  recovery_procedures:
    database_corruption:
      - restore_from_backup
      - rebuild_indexes
      - verify_integrity

    configuration_loss:
      - restore_from_backup
      - validate_syntax
      - reload_configuration
```

### Integration Settings

```yaml
# configs/advanced/integrations.yaml
integrations:
  external_apis:
    timeout_seconds: 30
    retry_attempts: 3
    retry_delay_seconds: 5

  webhooks:
    enabled: true
    endpoints:
      workflow_complete: https://external.example.com/webhook/workflow
      server_provisioned: https://external.example.com/webhook/server

    security:
      signature_header: X-HWAutomation-Signature
      secret_env: WEBHOOK_SECRET

  notifications:
    slack:
      enabled: false
      webhook_url_env: SLACK_WEBHOOK_URL
      channel: "#hwautomation"

    email:
      enabled: false
      smtp_server: smtp.example.com
      smtp_port: 587
      username_env: SMTP_USERNAME
      password_env: SMTP_PASSWORD
      from_address: hwautomation@example.com
```

---

*For additional configuration examples and templates, see the `configs/` directory in the repository.*
