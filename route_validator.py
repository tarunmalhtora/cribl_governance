import sys
import json

def validate_route(name, destination):
    if "splunk" in destination.lower():
        if not name.startswith("SPLUNK -"):
            return False, f"❌ FAIL: Route '{name}' → Destination '{destination}' → Should start with 'SPLUNK - <Tenant Name>'"
        else:
            return True, f"✅ PASS: Route '{name}' is correctly named for Splunk."
    elif "opensearch" in destination.lower():
        if not name.startswith("NEO AUTO -"):
            return False, f"❌ FAIL: Route '{name}' → Destination '{destination}' → Should start with 'NEO AUTO - <Tenant Name>' (NEO Output Router)"
        else:
            return True, f"✅ PASS: Route '{name}' is correctly named for OpenSearch."
    else:
        return True, f"ℹ️ SKIP: Destination '{destination}' not validated."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 route_validator.py routes.json")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        routes = json.load(f)

    print("\n--- Route Naming Convention Validation ---")
    for route in routes:
        passed, msg = validate_route(route["name"], route["destination"])
        print(msg)
    print("------------------------------------------\n")
