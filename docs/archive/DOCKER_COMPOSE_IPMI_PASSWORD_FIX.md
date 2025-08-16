# Docker Compose IPMI Password Fix

## Issue Description
When running `sudo make up`, Docker Compose was showing warnings:
```
WARN[0000] The "n0hOpe" variable is not set. Defaulting to a blank string.
```

## Root Cause
The IPMI password in `.env` file contained a dollar sign (`$`) which Docker Compose interprets as variable substitution:
```bash
IPMI_PASSWORD=th3rE1$n0hOpe
```

Docker Compose was trying to substitute `$n0hOpe` as a variable, but this variable wasn't defined, causing the warning.

## Solution
Escaped the dollar sign by doubling it in the `.env` file:
```bash
# Before (causing warnings):
IPMI_PASSWORD=th3rE1$n0hOpe

# After (fixed):
IPMI_PASSWORD=th3rE1$$n0hOpe
```

## Verification
1. Docker Compose warnings are gone
2. IPMI password is correctly loaded in the container as `th3rE1$n0hOpe`
3. All services start successfully without warnings

## Docker Compose Variable Escaping Rules
- Single `$` triggers variable substitution
- Double `$$` escapes to a literal `$`
- Variables can be referenced as `${VARIABLE}` or `$VARIABLE`
- Use `$$` when you need a literal dollar sign in environment values

## Files Modified
- `.env` - Escaped the dollar sign in IPMI_PASSWORD

## Status
✅ **RESOLVED** - Docker Compose now starts without warnings and IPMI password is correctly configured.
