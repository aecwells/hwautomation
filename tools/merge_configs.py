#!/usr/bin/env python3
"""
Merge generated device mappings with existing ones and copy relevant XML templates
"""

import yaml
import shutil
import os
from pathlib import Path

def merge_device_mappings():
    """Merge generated device mappings with existing ones"""
    
    # Load existing mappings
    try:
        with open('configs/bios/device_mappings.yaml', 'r') as f:
            existing = yaml.safe_load(f)
    except FileNotFoundError:
        existing = {'device_types': {}}
    
    # Load generated mappings
    with open('configs/bios/device_mappings_generated.yaml', 'r') as f:
        generated = yaml.safe_load(f)
    
    # Create backup of existing file
    shutil.copy2('configs/bios/device_mappings.yaml', 'configs/bios/device_mappings.yaml.backup')
    print("✅ Created backup: device_mappings.yaml.backup")
    
    # Merge configurations (generated will override existing for same keys)
    merged_types = existing['device_types'].copy()
    
    # Focus on server types that match common patterns or are Supermicro-based
    priority_servers = []
    supermicro_servers = []
    
    for server_id, config in generated['device_types'].items():
        vendor = config.get('hardware_specs', {}).get('vendor', '').lower()
        
        # Prioritize existing naming patterns (s1, s2, s3, etc.) and Supermicro
        if (server_id.startswith(('s1.', 's2.', 's3.', 's4.', 's5.')) or 
            vendor == 'supermicro' or
            server_id in ['d1.c1.small', 'd1.c1.medium', 'd1.c1.large']):
            priority_servers.append((server_id, config))
        elif vendor == 'supermicro':
            supermicro_servers.append((server_id, config))
    
    # Add priority servers first
    for server_id, config in priority_servers:
        merged_types[server_id] = config
        print(f"  + Added {server_id}: {config['description']}")
    
    # Add some key Supermicro servers
    for server_id, config in supermicro_servers[:10]:  # Limit to first 10
        if server_id not in merged_types:
            merged_types[server_id] = config
            print(f"  + Added {server_id}: {config['description']}")
    
    # Save merged mappings
    merged_config = {'device_types': merged_types}
    with open('configs/bios/device_mappings.yaml', 'w') as f:
        yaml.dump(merged_config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Merged device mappings: {len(merged_types)} total device types")
    return list(merged_types.keys())

def copy_xml_templates(device_types):
    """Copy relevant XML templates to the main templates directory"""
    
    source_dir = Path('configs/bios/xml_templates_generated')
    target_dir = Path('configs/bios/xml_templates')
    
    # Create backup of existing templates
    if target_dir.exists():
        backup_dir = Path('configs/bios/xml_templates_backup')
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.copytree(target_dir, backup_dir)
        print("✅ Created backup: xml_templates_backup/")
    
    target_dir.mkdir(exist_ok=True)
    
    copied_count = 0
    for device_type in device_types:
        source_file = source_dir / f"{device_type}.xml"
        target_file = target_dir / f"{device_type}.xml"
        
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            copied_count += 1
            print(f"  → Copied {device_type}.xml")
        else:
            print(f"  ⚠️  Template not found for {device_type}")
    
    print(f"✅ Copied {copied_count} XML templates")

def update_orchestration_dropdown(device_types):
    """Update the orchestration.html dropdown with new device types"""
    
    orchestration_file = 'gui/templates/orchestration.html'
    
    # Create backup
    shutil.copy2(orchestration_file, orchestration_file + '.backup')
    print("✅ Created backup: orchestration.html.backup")
    
    # Read the file
    with open(orchestration_file, 'r') as f:
        content = f.read()
    
    # Find the device type dropdown section
    dropdown_start = content.find('<select class="form-select" id="deviceType"')
    dropdown_end = content.find('</select>', dropdown_start) + 9
    
    if dropdown_start == -1:
        print("⚠️  Could not find device type dropdown in orchestration.html")
        return
    
    # Build new dropdown options
    options = ['                        <option value="">Select device type...</option>']
    
    # Group by series for better organization
    series_groups = {}
    for device_type in sorted(device_types):
        if '.' in device_type:
            series = device_type.split('.')[0]
            if series not in series_groups:
                series_groups[series] = []
            series_groups[series].append(device_type)
        else:
            # Handle legacy naming (underscores)
            if 'legacy' not in series_groups:
                series_groups['legacy'] = []
            series_groups['legacy'].append(device_type)
    
    # Add options by series
    for series in sorted(series_groups.keys()):
        if series != 'legacy':
            options.append(f'                        <optgroup label="{series.upper()} Series">')
        
        for device_type in sorted(series_groups[series]):
            options.append(f'                        <option value="{device_type}">{device_type}</option>')
        
        if series != 'legacy':
            options.append('                        </optgroup>')
    
    # Build new dropdown HTML
    new_dropdown = f'''<select class="form-select" id="deviceType" required>
{chr(10).join(options)}
                    </select>'''
    
    # Replace in content
    new_content = content[:dropdown_start] + new_dropdown + content[dropdown_end:]
    
    # Write back
    with open(orchestration_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated orchestration dropdown with {len(device_types)} device types")

def main():
    print("🔧 Merging generated configurations with existing ones...")
    
    # Merge device mappings
    device_types = merge_device_mappings()
    
    # Copy XML templates
    copy_xml_templates(device_types)
    
    # Update orchestration dropdown
    update_orchestration_dropdown(device_types)
    
    print(f"\n🎉 Integration complete!")
    print(f"✅ Merged {len(device_types)} device types")
    print("✅ XML templates copied")
    print("✅ Orchestration dropdown updated")
    
    print("\n📋 Available Device Types:")
    for device_type in sorted(device_types)[:15]:  # Show first 15
        print(f"  • {device_type}")
    if len(device_types) > 15:
        print(f"  ... and {len(device_types) - 15} more")
    
    print("\n🚀 Your BIOS automation system now has comprehensive device support!")
    print("   Test by starting a provisioning workflow with the new device types.")

if __name__ == "__main__":
    main()
