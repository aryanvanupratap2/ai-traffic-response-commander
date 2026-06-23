# utils/copilot.py

def generate_copilot_response(report):

    impact = report["Impact Class"]
    delay = report["Delay Seconds"]
    roads = report["Affected Roads"]
    junctions = report["Critical Junctions"]
    police = report["Police Deployment"]
    recommendation = report["Recommendation"]
    route_changed = report["Route Changed"]

    # ------------------------------------------------
    # Risk Assessment
    # ------------------------------------------------

    if impact == "High":

        severity = "🔴 HIGH"

        risk_summary = (
            "Major disruption expected across the road network."
        )

        priority = "Immediate Action Required"

    elif impact == "Medium":

        severity = "🟠 MEDIUM"

        risk_summary = (
            "Moderate congestion likely around the incident zone."
        )

        priority = "Monitor Closely"

    else:

        severity = "🟢 LOW"

        risk_summary = (
            "Minor localized traffic impact."
        )

        priority = "Routine Monitoring"

    # ------------------------------------------------
    # Delay Analysis
    # ------------------------------------------------

    if delay > 1000:

        delay_comment = (
            "Severe travel delays expected."
        )

    elif delay > 300:

        delay_comment = (
            "Moderate travel delays expected."
        )

    else:

        delay_comment = (
            "Minimal travel delay expected."
        )

    # ------------------------------------------------
    # Diversion Strategy
    # ------------------------------------------------

    if route_changed:

        diversion = (
            "Alternative routes should be activated immediately."
        )

    else:

        diversion = (
            "Current routes remain usable."
        )

    # ------------------------------------------------
    # Police Strategy
    # ------------------------------------------------

    if police >= 15:

        police_strategy = (
            "Deploy traffic teams at all major junctions."
        )

    elif police >= 8:

        police_strategy = (
            "Deploy officers at congestion hotspots."
        )

    else:

        police_strategy = (
            "Small response team is sufficient."
        )

    # ------------------------------------------------
    # Final Response
    # ------------------------------------------------

    response = f"""
## 🤖 AI Traffic Copilot

### Situation Summary

Impact Level: {severity}

{risk_summary}

### Traffic Analysis

• Affected Roads: {roads}

• Critical Junctions: {junctions}

• Estimated Delay: {delay:.2f} sec

• Route Diversion Needed: {route_changed}

### Delay Assessment

{delay_comment}

### Police Deployment Plan

Required Officers: {police}

{police_strategy}

### Diversion Strategy

{diversion}

### Recommended Action

{recommendation}

### Operational Priority

{priority}

### Public Advisory

Motorists should avoid the incident zone
and use navigation-assisted alternative routes.
"""

    return response