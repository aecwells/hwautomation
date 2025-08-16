#!/bin/bash
# Tools Cleanup Script - Remove unused/redundant tools
# Keep only essential development tools

set -e

TOOLS_DIR="tools"
BACKUP_DIR="tools/archive"

echo "=== HWAutomation Tools Cleanup ==="
echo "This script will archive unused tools and keep only essentials"
echo ""

# Create archive directory
mkdir -p "$BACKUP_DIR"

# Essential tools to keep (don't move these)
ESSENTIAL_TOOLS=(
    "release.py"
    "generate_changelog.py"
    "quality/code_quality.py"
    "setup/setup_dev.py"
    "README.md"
)

# Function to check if a file is essential
is_essential() {
    local file="$1"
    for essential in "${ESSENTIAL_TOOLS[@]}"; do
        if [[ "$file" == *"$essential"* ]]; then
            return 0  # Essential
        fi
    done
    return 1  # Not essential
}

echo "Identifying files to archive..."

# Find all Python files in tools directory
find "$TOOLS_DIR" -name "*.py" -type f | while read -r file; do
    # Skip if it's already in archive
    if [[ "$file" == *"/archive/"* ]]; then
        continue
    fi

    # Skip essential tools
    if is_essential "$file"; then
        echo "KEEP: $file (essential)"
        continue
    fi

    # Check if it's a demo/test/phase file (likely not needed)
    if [[ "$file" == *"demo"* ]] || [[ "$file" == *"test_"* ]] || [[ "$file" == *"phase"* ]] || [[ "$file" == *"example"* ]]; then
        rel_path=${file#$TOOLS_DIR/}
        dest_path="$BACKUP_DIR/$rel_path"
        dest_dir=$(dirname "$dest_path")

        echo "ARCHIVE: $file -> $dest_path"

        # Create destination directory
        mkdir -p "$dest_dir"

        # Move file to archive
        mv "$file" "$dest_path"
        continue
    fi

    echo "REVIEW: $file (manual review needed)"
done

echo ""
echo "=== Cleanup Summary ==="
echo "Essential tools preserved in $TOOLS_DIR/"
echo "Archived tools moved to $BACKUP_DIR/"
echo ""
echo "Essential tools kept:"
for tool in "${ESSENTIAL_TOOLS[@]}"; do
    if [[ -f "$TOOLS_DIR/$tool" ]]; then
        echo "  ✓ $TOOLS_DIR/$tool"
    else
        echo "  ✗ $TOOLS_DIR/$tool (missing)"
    fi
done

echo ""
echo "To restore an archived tool: mv $BACKUP_DIR/<tool> $TOOLS_DIR/<tool>"
echo "To permanently delete archived tools: rm -rf $BACKUP_DIR/"
