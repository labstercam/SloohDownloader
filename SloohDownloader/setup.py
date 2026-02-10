# Slooh Downloader - Setup Script
# Run this to verify IronPython and .NET dependencies

import clr
import sys

print("="* 60)
print(" Slooh Downloader - Setup and Dependency Check")
print("=" * 60)
print()

# Check IronPython version
print("IronPython Version: {0}".format(sys.version))
print("Implementation: {0}".format(sys.implementation.name if hasattr(sys, 'implementation') else 'IronPython'))
print()

# Check .NET references
dependencies = [
    ('System', 'Core .NET framework'),
    ('System.Net.Http', 'HTTP client for API communication'),
    ('System.IO', 'File system operations'),
    ('System.Threading', 'Multi-threading support')
]

print("Checking .NET dependencies:")
print()

all_ok = True

for ref, description in dependencies:
    try:
        clr.AddReference(ref)
        print("  [OK] {0} - {1}".format(ref, description))
    except Exception as e:
        print("  [FAIL] {0} - {1}".format(ref, str(e)))
        all_ok = False

print()

# Check SQLite (optional for Stage 1, required for Stage 2)
print("Checking optional dependencies:")
try:
    clr.AddReference('System.Data.SQLite')
    print("  [OK] System.Data.SQLite - Database support")
    print("       (Required for Stage 2 and later)")
except:
    print("  [WARNING] System.Data.SQLite not found")
    print("       This is OK for Stage 1 (Configuration & Authentication)")
    print("       Will be needed for Stage 2 (Database & Tracking)")
    print("       Install from: https://system.data.sqlite.org/")

print

# Test JSON module
try:
    import json
    test_data = {'test': 'value'}
    json.dumps(test_data)
    print("  [OK] json - JSON serialization")
except Exception as e:
    print("  [FAIL] json - {0}".format(str(e)))
    all_ok = False

print()
print("=" * 60)

if all_ok:
    print(" Setup Complete - Ready for Stage 1 Development")
    print(" Run: ipy src/main.py --help")
else:
    print(" Setup INCOMPLETE - Some dependencies missing")
    print(" Please install missing dependencies before proceeding")

print("=" * 60)
