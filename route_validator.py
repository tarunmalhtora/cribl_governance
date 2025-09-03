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


def check_naming(route_dict):
    """Check route naming convention based on destination."""
    print(f"routeName => {(routeName := route_dict['routeName'])}")
    print(f"destination => {(destination := route_dict['destination'])}")
    
    # final_status, errors, warnings = [], [], []

    # print(f"[DEBUG] Checking route '{name}' with destination '{dest}'")
    Validation_Status = []
    status = "Pass"
    remarks = "NA"

    if "opensearch" in destination.lower():
        print("checking validation for OpenSearch")
        if not (routeName.startswith("NEO AUTO - ") and routeName.endswith("(NEO Output Router)")):
            status = "Failed"
            Validation_Status.append(
                f"Route '{routeName}' is INVALID for OpenSearch. "
                "Must be in format: 'NEO AUTO - <tenant name> (NEO Output Router)'.")
            remarks = Validation_Status
        else:
            Validation_Status.append(f"✅ Route name validation is passed ✅ ")
             
        

    elif "splunk" in destination.lower():
        print("checking validation for Splunk")
        if not routeName.startswith("SPLUNK - "):
            status = "Failed"
            Validation_Status.append(
                f"Route '{routeName}' is INVALID for Splunk. "
                "Must be in format: 'SPLUNK - <tenant name>'.")
            remarks = Validation_Status
        else:
            Validation_Status.append(f"✅ Route name validation is passed ✅ ")
    else:
        status = "Failed"
        remarks = f"Unsupported destination '{destination}' for naming convention validation."
        print(f"Unsupported destination '{destination}' for naming convention validation.")
        
    print("Validation_Status",Validation_Status)
    
    return {"No": 1, "Check Name": "Route Naming Validation", "Status": status, "Remarks": remarks}


def write_text_table(results, filename="validation_report.txt"):
    """Write results into a table-style text file."""
    with open(filename, "w") as f:
        f.write("No. | Check Name        | Status  | Remarks\n")
        f.write("----|-------------------|---------|-----------------------------------------------------------\n")
        for r in results:
            f.write(f"{r['No']:<3} | {r['Check Name']:<17} | {r['Status']:<7} | {r['Remarks']}\n")
    print(f"\n📄 Validation report written to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 route_validator.py <routes.json>")
        sys.exit(1)

    input_file = sys.argv[1]
    try:
        with open(input_file) as f:
            routes = json.load(f)
            print(f" File read successfull {routes}")
        route_dict = routes[0]
        print("verify the data type", type(route_dict))
    except Exception as e:
        print(f"❌ Failed to read input file '{input_file}': {e}")
        sys.exit(1)

    print(f"✅ Loaded {len(routes)} route(s) from {input_file} for further validation")
    
    result = check_naming(route_dict)
    print("Final check to be passed : ", result)

    # ✅ Write JSON report instead of text table
    with open("validation_report.json", "w") as f:
        json.dump([result], f, indent=2)

    print("📄 Validation report written to validation_report.json")
