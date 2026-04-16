"""
Scoring engine: produces a flat list of findings from all audit data.
Also computes per-category and overall compliance scores.
"""

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Pass": 4}


def score_all(data: dict) -> list:
    """
    Returns a list of finding dicts:
        category, severity, description, recommended_action, compliant (bool)
    Passing checks are included with severity='Pass' and compliant=True.
    """
    findings = []
    findings.extend(_score_external_sharing(data["external_sharing"]))
    findings.extend(_score_admin_roles(data["admin_roles"]))
    findings.extend(_score_mfa(data["mfa"]))
    findings.extend(_score_dlp(data["dlp"]))
    findings.extend(_score_vault(data["vault"], data["suspended_users"]))
    return findings


def compute_scores(findings: list) -> dict:
    """
    Returns overall and per-category compliance scores (0-100).
    """
    categories = {}
    for f in findings:
        cat = f["category"]
        if cat not in categories:
            categories[cat] = {"pass": 0, "total": 0}
        categories[cat]["total"] += 1
        if f["compliant"]:
            categories[cat]["pass"] += 1

    per_category = {}
    for cat, counts in categories.items():
        per_category[cat] = (
            round(counts["pass"] / counts["total"] * 100) if counts["total"] > 0 else 100
        )

    total_checks = sum(c["total"] for c in categories.values())
    passing_checks = sum(c["pass"] for c in categories.values())
    overall = round(passing_checks / total_checks * 100) if total_checks > 0 else 100

    return {"overall": overall, "by_category": per_category}


def top_critical_findings(findings: list, n: int = 5) -> list:
    failing = [f for f in findings if not f["compliant"]]
    failing.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))
    return failing[:n]


# ---------------------------------------------------------------------------
# Per-category scorers
# ---------------------------------------------------------------------------


def _score_external_sharing(records: list) -> list:
    findings = []
    for item in records:
        if item["share_type"] == "anyone_with_link":
            findings.append({
                "category": "External Sharing",
                "severity": "High",
                "description": f"'{item['file_name']}' shared with anyone who has the link",
                "recommended_action": item["recommended_action"],
                "compliant": False,
            })
        elif item["share_type"] == "personal_gmail":
            findings.append({
                "category": "External Sharing",
                "severity": "High",
                "description": f"'{item['file_name']}' shared with a personal Gmail account",
                "recommended_action": item["recommended_action"],
                "compliant": False,
            })
        elif item["share_type"] == "external_member":
            findings.append({
                "category": "External Sharing",
                "severity": "Medium",
                "description": f"Shared drive '{item['file_name']}' has external member access",
                "recommended_action": item["recommended_action"],
                "compliant": False,
            })

    # Add a pass entry for clean sharing if no items flagged
    if not records:
        findings.append({
            "category": "External Sharing",
            "severity": "Pass",
            "description": "No externally shared Drive items found",
            "recommended_action": "",
            "compliant": True,
        })

    return findings


def _score_admin_roles(admins: list) -> list:
    findings = []

    super_admins = [a for a in admins if a["role"] == "Super Admin"]
    non_service_super_admins = [
        a for a in super_admins if "Service Account" not in a.get("ou", "")
    ]

    # Emit per-account findings for flagged accounts
    seen_emails = set()
    for admin in admins:
        if admin["flag_reason"] and admin["email"] not in seen_emails:
            seen_emails.add(admin["email"])
            findings.append({
                "category": "Admin Roles",
                "severity": admin["severity"],
                "description": f"{admin['email']} ({admin['role']}): {admin['flag_reason']}",
                "recommended_action": _admin_remediation(admin["severity"]),
                "compliant": False,
            })

    # Aggregate finding for super admin count
    count = len(non_service_super_admins)
    if count > 2:
        extra = count - 2
        findings.append({
            "category": "Admin Roles",
            "severity": "Low",
            "description": f"{count} Super Admin accounts active ({extra} above recommended maximum of 2)",
            "recommended_action": "Review Super Admin assignments and revoke where not operationally required",
            "compliant": False,
        })
    else:
        findings.append({
            "category": "Admin Roles",
            "severity": "Pass",
            "description": f"Super Admin count ({count}) is within recommended limit",
            "recommended_action": "",
            "compliant": True,
        })

    return findings


def _admin_remediation(severity: str) -> str:
    if severity == "Critical":
        return "Remove Super Admin role from service account and use a least-privilege custom role instead"
    if severity == "High":
        return "Disable or deprovision inactive admin account; review if access is still required"
    return "Review admin assignment and remove if no longer needed"


def _score_mfa(mfa: dict) -> list:
    findings = []
    threshold = mfa["threshold_pct"]

    # Overall enrollment
    if mfa["overall_enrollment_pct"] < threshold:
        findings.append({
            "category": "MFA Enforcement",
            "severity": "High",
            "description": (
                f"Overall 2SV enrollment is {mfa['overall_enrollment_pct']:.1f}%, "
                f"below the {threshold:.0f}% compliance threshold"
            ),
            "recommended_action": "Enforce mandatory 2SV in the Admin console and send enrollment reminders",
            "compliant": False,
        })
    else:
        findings.append({
            "category": "MFA Enforcement",
            "severity": "Pass",
            "description": f"Overall 2SV enrollment ({mfa['overall_enrollment_pct']:.1f}%) meets the {threshold:.0f}% threshold",
            "recommended_action": "",
            "compliant": True,
        })

    # Per-OU
    for ou in mfa["by_ou"]:
        if ou["pct"] < 80.0:
            findings.append({
                "category": "MFA Enforcement",
                "severity": "High",
                "description": f"OU '{ou['ou']}' has only {ou['pct']:.1f}% 2SV enrollment (below 80%)",
                "recommended_action": f"Enforce mandatory 2SV for the {ou['ou']} OU immediately",
                "compliant": False,
            })
        elif ou["pct"] < threshold:
            findings.append({
                "category": "MFA Enforcement",
                "severity": "Medium",
                "description": f"OU '{ou['ou']}' is at {ou['pct']:.1f}% 2SV enrollment (below {threshold:.0f}% threshold)",
                "recommended_action": f"Send 2SV enrollment reminders to remaining users in {ou['ou']}",
                "compliant": False,
            })
        else:
            findings.append({
                "category": "MFA Enforcement",
                "severity": "Pass",
                "description": f"OU '{ou['ou']}' meets the 2SV enrollment threshold ({ou['pct']:.1f}%)",
                "recommended_action": "",
                "compliant": True,
            })

    # Users without 2SV and no exception
    undocumented = [u for u in mfa["unenrolled_users"] if not u["exception_documented"]]
    if undocumented:
        findings.append({
            "category": "MFA Enforcement",
            "severity": "Medium",
            "description": (
                f"{len(undocumented)} user(s) have no 2SV enrollment and no documented exception"
            ),
            "recommended_action": "Require 2SV enrollment for these users or add a formal exception with approval",
            "compliant": False,
        })

    return findings


def _score_dlp(dlp: dict) -> list:
    findings = []

    for ou in dlp.get("uncovered_ous", []):
        findings.append({
            "category": "DLP Coverage",
            "severity": "High",
            "description": f"OU '{ou['ou']}' has no DLP rule coverage",
            "recommended_action": "Apply relevant DLP rules (PCI, PII, or custom) to this OU in the Admin console",
            "compliant": False,
        })

    for rule in dlp.get("audit_only_rules", []):
        findings.append({
            "category": "DLP Coverage",
            "severity": "Medium",
            "description": f"DLP rule '{rule['name']}' is in audit-only mode and is not actively blocking",
            "recommended_action": rule["recommendation"],
            "compliant": False,
        })

    for rule in dlp.get("rules", []):
        if rule["mode"] == "enforcing":
            findings.append({
                "category": "DLP Coverage",
                "severity": "Pass",
                "description": f"DLP rule '{rule['name']}' is actively enforcing",
                "recommended_action": "",
                "compliant": True,
            })

    if not dlp.get("rules"):
        findings.append({
            "category": "DLP Coverage",
            "severity": "Pass",
            "description": "No DLP data available (live mode only)",
            "recommended_action": "",
            "compliant": True,
        })

    return findings


def _score_vault(vault: dict, suspended_users: list) -> list:
    findings = []

    for ou in vault.get("ous_without_rule", []):
        findings.append({
            "category": "Vault Retention",
            "severity": "Medium",
            "description": f"OU '{ou}' has no explicit Vault retention rule defined",
            "recommended_action": "Define a retention policy for this OU in Google Vault",
            "compliant": False,
        })

    for ou in vault.get("all_ous", []):
        if ou not in vault.get("ous_without_rule", []):
            findings.append({
                "category": "Vault Retention",
                "severity": "Pass",
                "description": f"OU '{ou}' has an explicit retention rule",
                "recommended_action": "",
                "compliant": True,
            })

    # Suspended users with active group memberships
    for user in suspended_users:
        if user["group_memberships"] > 0:
            findings.append({
                "category": "Vault Retention",
                "severity": "Medium",
                "description": (
                    f"Suspended user {user['email']} is a member of "
                    f"{user['group_memberships']} active Google Group(s)"
                ),
                "recommended_action": "Remove suspended user from all Google Groups via the Admin console",
                "compliant": False,
            })

    # Suspended users with drive edit access
    for user in suspended_users:
        if user["drive_edit_access"] > 0:
            findings.append({
                "category": "External Sharing",
                "severity": "High",
                "description": (
                    f"Suspended user {user['email']} has edit access to "
                    f"{user['drive_edit_access']} shared drive(s)"
                ),
                "recommended_action": "Remove suspended user from all shared drives immediately",
                "compliant": False,
            })

    return findings
