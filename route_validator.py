"""
route_validator.py

Stage 1: Naming Convention Validation
-------------------------------------
Rules:
1. If destination contains 'opensearch':
   Route name must start with "NEO AUTO - " 
   AND end with "(NEO Output Router)".

   Example:  "NEO AUTO - nmp_dev (NEO Output Router)"  ✅

2. If destination contains 'splunk':
   Route name must start with "SPLUNK - ".

   Example:  "SPLUNK - hiport"  ✅
"""

import json
import sys
import traceback


def check_naming(route):
    """Check route naming convention based on destination."""
    name = route.get("name", "").strip()
    dest = route.get("destination", "").strip()

    errors, warnings = [], []

    print(f"[DEBUG] Checking route '{name}' with destination '{dest}'")

    if "opensearch" in dest.lower():
        if not (name.startswith("NEO AUTO - ") and name.endswith("(NEO Output Router)")):
            errors.append(
                f"Route '{name}' is INVALID for OpenSearch. "
                "Must be in format: 'NEO AUTO - <tenant> (NEO Output Router)'."
            )

    elif "splunk" in dest.lower():
        if not name.startswith("SPLUNK - "):
            errors.append(
                f"Route '{name}' is INVALID for Splunk. "
                "Must be in format: 'SPLUNK - <tenant>'."
            )

    else:
        warnings.append(f"Destination '{dest}' not recognized. No naming rules applied.")

    return errors, warnings


def validate_routes(routes):
    results = []

    for r in routes:
        route_result = {
            "route_name": r.get("name"),
            "destination": r.get("destination"),
            "is_valid": True,
            "errors": [],
            "warnings": []
        }

        try:
            errs, warns = check_naming(r)
            route_result["errors"].extend(errs)
            route_result["warnings"].extend(warns)

            if route_result["errors"]:
                route_result["is_valid"] = False

        except Exception as e:
            tb = traceback.format_exc()
            route_result["is_valid"] = False
            route_result["errors"].append(f"Validator crashed: {str(e)}")
            route_result["errors"].append(tb)

        results.append(route_result)

    return results


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 route_validator.py <routes.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        with open(input_file) as f:
            routes = json.load(f)
    except Exception as e:
        print(f"❌ Failed to read input file '{input_file}': {e}")
        sys.exit(1)

    print(f"✅ Loaded {len(routes)} route(s) from {input_file}")

    # Run validation
    results = validate_routes(routes)

    # Print human-friendly summary
    print("\n📋 Validation Results:")
    for r in results:
        mark = "✅" if r["is_valid"] else "❌"
        print(f"{mark} Route '{r['route_name']}' (Destination: {r['destination']})")
        for err in r["errors"]:
            print(f"   - [ERROR] {err}")
        for warn in r["warnings"]:
            print(f"   - [WARN]  {warn}")

    # Write JSON report
    out_file = "validation_report.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    # Exit with status
    if any(not r["is_valid"] for r in results):
        sys.exit(1)
    else:
        sys.exit(0)
