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
import re


def check_naming(route_dict):
    """Check route naming convention based on destination."""
    print(f"routeName => {(routeName := route_dict['routeName'])}")
    print(f"destination => {(destination := route_dict['destination'])}")
    
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


def check_filter_basic(route_dict):
    """
    Validate the filter field in the route_dict.
    Rules enforced:
      - Must be present and non-empty string
      - No forbidden characters (null, newline, backtick, semicolon)
      - Quotes must be balanced
      - Parentheses must be balanced
      - 'in' operator not allowed
      - Single '=' not allowed (must use '==')
      - Must reference both 'index' and '__inputId'
      - Allowed forms:
          * index == 'value'  or index == "value"
          * index == value (allowed but warns to quote RHS)
          * index.includes('value') or index.includes("value")
      - Wildcard '*' is not allowed in RHS (quoted or inside includes)
    """

    REQUIRE_INDEX = True
    REQUIRE_INPUTID = True
    check_name = "Filter Presence & Syntax"

    # --------- Step 1: Get filter value ---------
    f = route_dict.get("filter", None)
    print(f"[DEBUG] Raw filter value => {f!r}")

    # --------- Step 2: Presence checks ---------
    if f is None:
        return {"Check Name": check_name, "Status": "Failed", "Remarks": "Filter key missing."}
    if not isinstance(f, str) or not f.strip():
        return {"Check Name": check_name, "Status": "Failed", "Remarks": "Filter is empty or only whitespace."}
    print("[DEBUG] Passed presence check")

    s = f.strip()
    print(f"[DEBUG] Normalized filter string after strip => {s}")

    # --------- Step 3: Length & forbidden characters ---------
    MAX_LEN = 2000
    print("2. length is", len(s))
    if len(s) > MAX_LEN:
        return {"Check Name": check_name, "Status": "Failed", "Remarks": f"Filter too long (> {MAX_LEN} chars)."}

    forbidden_chars = ['\x00', '\r', '\n', '`', ';']
    bad = [c for c in forbidden_chars if c in s]
    if bad:
        return {"Check Name": check_name, "Status": "Failed","Remarks": f"Contains forbidden characters: {', '.join(repr(c) for c in bad)}"}
    print("[DEBUG] Passed length and forbidden character checks")

    # --------- Step 4: Balanced quotes ---------
    def quotes_balanced(st, quote_char):
        i = 0
        count = 0
        while i < len(st):
            if st[i] == "\\":
                i += 2
                continue
            if st[i] == quote_char:
                count += 1
            i += 1
        return (count % 2) == 0

    if not quotes_balanced(s, "'") or not quotes_balanced(s, '"'):
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Unbalanced quotes in filter (single or double)."}
    print("[DEBUG] Passed balanced quotes check")

    # ✅ Balanced parentheses check
    if s.count("(") != s.count(")"):
        return {"Check Name": check_name, "Status": "Failed",
                "Remarks": "Unbalanced parentheses in filter (check matching '(' and ')' )."}

    print("[DEBUG] Passed balanced quotes & parentheses check")

    # --------- Step 5: Operator sanity ---------
    if re.search(r"\b in \b", s, flags=re.IGNORECASE):
        print("[DEBUG] Found unsupported 'in' operator")
        return {"Check Name": check_name, "Status": "Failed", "Remarks": "Operator 'in' is not supported for index checks."}

    if re.search(r"(?<![=!<>])=(?!=)", s):
        print("[DEBUG] Found invalid single '='")
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Single '=' operator is not supported; use '==' for equality."}

    # Disallow single & or | (must use && or ||)
    if re.search(r"(^|[^&])&($|[^&])", s) or re.search(r"(^|[^|])\|($|[^|])", s):
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Invalid boolean operator; use '&&' or '||' instead of single & or |."}
    
    # Fail if dangling && or || at the end
    if re.search(r"(&&|\|\|)\s*$", s):
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Dangling boolean operator at end of filter."}

    # Invalid boolean sequence
    if re.search(r"(&&\s*\|\||\|\|\s*&&)", s):
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Invalid boolean operator sequence (e.g. '&& ||')."}

    print("[DEBUG] Passed operator checks")

    # --------- Step 6: Normalize spacing ---------
    norm = re.sub(r"\s+", " ", s)
    print(f"[DEBUG] Whitespace-normalized filter => {norm}")

    found_index_clause = False
    found_inputid_clause = False
    warnings = []

    # --------- Step 7: Match patterns ---------
    operator_pattern = r"(==|!=|>=|<=|>|<)"

    # 7a. index OP 'value' or "value" (quoted RHS with single or double quotes)
    m1 = re.search(rf"\bindex\b\s*{operator_pattern}\s*(['\"])([^'\"]*)\1", norm, flags=re.IGNORECASE)
    print(f"[DEBUG] Match m1 (quoted equality) => {bool(m1)}, {m1}")
    if m1:
        op = m1.group(1)  # operator (==, !=, etc.)
        val = m1.group(2) # RHS value inside quotes
        print(f"[DEBUG] Quoted RHS with operator {op} => {val}")
        if '*' in val:
            return {"Check Name": check_name, "Status": "Failed","Remarks": "Wildcard '*' usage in index value is not allowed."}
        found_index_clause = True

    # 7b. index OP value (unquoted RHS)
    m2 = re.search(rf"\bindex\b\s*{operator_pattern}\s*([A-Za-z0-9_.-]+)\b", norm, flags=re.IGNORECASE)
    if m2 and not m1:
        op = m2.group(1)
        val = m2.group(2)
        print(f"[DEBUG] Unquoted RHS with operator {op} => {val}")
        found_index_clause = True
        warnings.append(f"index compared using {op} with unquoted value; recommend quoting the RHS (single or double).")

    # 7c. index.includes(...)
    m3 = re.search(r"\bindex\b\.includes\s*\(\s*(['\"])(.*?)\1\s*\)", norm, flags=re.IGNORECASE)
    print(f"[DEBUG] Match m3 (includes) => {bool(m3)}, {m3}")
    if m3:
        val = m3.group(2)
        print(f"[DEBUG] includes val => {val}")
        if '*' in val:
            return {"Check Name": check_name, "Status": "Failed","Remarks": "Wildcard '*' usage in index.includes(...) is not allowed."}
        found_index_clause = True

    # ---- NEW: malformed RHS check
    # ---- NEW: catch malformed/unrecognized RHS that contains '*' or other invalid chars ----
    # This covers cases like: index==*sdfd  OR index==sdf*d  (m1/m2 won't match these)
    # if we find index== followed by a token containing '*' (or other disallowed chars), fail with explicit msg
    m_malformed = re.search(rf"\bindex\b\s*{operator_pattern}\s*([^\s()]+)", norm, flags=re.IGNORECASE)
    if m_malformed and not (m1 or m2):
        rhs_token = m_malformed.group(2)
        print("[DEBUG] Malformed RHS token detected =>", rhs_token)
        # if it includes wildcard or other disallowed char -> fail with explicit msg
        if '*' in rhs_token:
            return {"Check Name": check_name, "Status": "Failed","Remarks": "Wildcard '*' usage in index value is not allowed."}
        if not re.match(r"^[A-Za-z0-9_.\-'\"]+$", rhs_token):
            return {"Check Name": check_name, "Status": "Failed","Remarks": "Malformed RHS in index comparison; expected quoted string or alphanumeric token."}

    # --------- Step 7d: __inputId mandatory check ---------
    m_input = re.search(r"__inputId\s*==", norm, flags=re.IGNORECASE)
    if m_input:
        found_inputid_clause = True
        print("[DEBUG] Found __inputId clause in filter")

    # --------- Step 8: Ensure both mandatory clauses ---------
    if REQUIRE_INDEX and not found_index_clause:
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Filter must include an index check (e.g. index == 'nmp_prod')."}

    if REQUIRE_INPUTID and not found_inputid_clause:
        return {"Check Name": check_name, "Status": "Failed","Remarks": "Filter must include an __inputId check (e.g. __inputId=='splunk:in_splunk_tcp')."}

    # --------- Step 9: Return ---------
    if warnings:
        return {"Check Name": check_name, "Status": "Pass", "Remarks": " ; ".join(warnings)}
    else:
        return {"Check Name": check_name, "Status": "Pass", "Remarks": "Filter index & inputId checks OK."}


def write_text_table(results, filename="validation_report.txt"):
    """Write results into a table-style text file."""
    with open(filename, "w") as f:
        f.write("No. | Check Name        | Status  | Remarks\n")
        f.write("----|-------------------|---------|-----------------------------------------------------------\n")
        for r in results:
            f.write(f"{r.get('No','-'):<3} | {r['Check Name']:<17} | {r['Status']:<7} | {r['Remarks']}\n")
    print(f"\n📄 Validation report written to {filename}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 route_validator.py <routes.json> [report.json]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "validation_report.json"

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
    
    result1 = check_naming(route_dict)
    result2 = check_filter_basic(route_dict)
    print("Final checks to be passed : ", result1, result2)

    # ✅ Write JSON report with unique filename
    with open(output_file, "w") as f:
        json.dump([result1, result2], f, indent=2)

    print(f"📄 Validation report written to {output_file}")
