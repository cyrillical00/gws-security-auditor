"""
Synthetic demo data for Apex Labs - a 200-person Series B SaaS company.
Returns data in the same shape as gws_connector.load_all().
"""


def load_all() -> dict:
    return {
        "org_name": "Apex Labs",
        "total_users": 200,
        "audit_timestamp": "2026-04-15T09:00:00Z",
        "external_sharing": _external_sharing(),
        "admin_roles": _admin_roles(),
        "mfa": _mfa(),
        "dlp": _dlp(),
        "vault": _vault(),
        "suspended_users": _suspended_users(),
    }


def _external_sharing() -> list:
    # 14 "anyone with link", 3 external member, 2 personal gmail
    anyone_with_link = [
        {
            "file_name": "Q1 2024 Financial Model.xlsx",
            "owner_ou": "Finance",
            "share_type": "anyone_with_link",
            "last_modified": "2024-03-15",
            "recommended_action": "Remove public link and restrict to domain users only",
            "severity": "High",
        },
        {
            "file_name": "Series B Pitch Deck v3.pptx",
            "owner_ou": "Executives",
            "share_type": "anyone_with_link",
            "last_modified": "2024-06-02",
            "recommended_action": "Remove public link and restrict to named collaborators",
            "severity": "High",
        },
        {
            "file_name": "Engineering Roadmap 2025.docx",
            "owner_ou": "Product",
            "share_type": "anyone_with_link",
            "last_modified": "2025-01-10",
            "recommended_action": "Remove public link and share via internal link only",
            "severity": "High",
        },
        {
            "file_name": "Customer Onboarding Tracker.gsheet",
            "owner_ou": "Customer Success",
            "share_type": "anyone_with_link",
            "last_modified": "2025-08-22",
            "recommended_action": "Remove public link and restrict to Customer Success OU",
            "severity": "High",
        },
        {
            "file_name": "AWS Cost Report - March 2025.pdf",
            "owner_ou": "Engineering",
            "share_type": "anyone_with_link",
            "last_modified": "2025-04-05",
            "recommended_action": "Remove public link and share only with Finance and Engineering leads",
            "severity": "High",
        },
        {
            "file_name": "Sales Compensation Plan FY2025.xlsx",
            "owner_ou": "Sales",
            "share_type": "anyone_with_link",
            "last_modified": "2025-01-15",
            "recommended_action": "Remove public link and restrict to Sales leadership",
            "severity": "High",
        },
        {
            "file_name": "Employee Directory Export.csv",
            "owner_ou": "IT/Admin",
            "share_type": "anyone_with_link",
            "last_modified": "2025-11-30",
            "recommended_action": "Remove immediately - PII exposure risk",
            "severity": "High",
        },
        {
            "file_name": "Incident Response Runbook.docx",
            "owner_ou": "Engineering",
            "share_type": "anyone_with_link",
            "last_modified": "2025-03-18",
            "recommended_action": "Remove public link and restrict to Engineering and IT/Admin",
            "severity": "High",
        },
        {
            "file_name": "Vendor NDA Template.docx",
            "owner_ou": "Legal/Compliance",
            "share_type": "anyone_with_link",
            "last_modified": "2025-06-09",
            "recommended_action": "Remove public link and share via approved legal channels",
            "severity": "High",
        },
        {
            "file_name": "Board Meeting Notes - Q3 2025.docx",
            "owner_ou": "Executives",
            "share_type": "anyone_with_link",
            "last_modified": "2025-10-12",
            "recommended_action": "Remove public link and restrict to executives and board members",
            "severity": "High",
        },
        {
            "file_name": "Hiring Pipeline - Engineering.gsheet",
            "owner_ou": "Product",
            "share_type": "anyone_with_link",
            "last_modified": "2025-09-25",
            "recommended_action": "Remove public link and restrict to HR and hiring managers",
            "severity": "High",
        },
        {
            "file_name": "Marketing Budget Allocation.xlsx",
            "owner_ou": "Marketing",
            "share_type": "anyone_with_link",
            "last_modified": "2025-12-01",
            "recommended_action": "Remove public link and restrict to Marketing and Finance",
            "severity": "High",
        },
        {
            "file_name": "Security Policy v2.1.pdf",
            "owner_ou": "IT/Admin",
            "share_type": "anyone_with_link",
            "last_modified": "2026-01-08",
            "recommended_action": "Remove public link - policy documents should be internal only",
            "severity": "High",
        },
        {
            "file_name": "Customer Data Processing Agreement.docx",
            "owner_ou": "Legal/Compliance",
            "share_type": "anyone_with_link",
            "last_modified": "2026-02-14",
            "recommended_action": "Remove public link and share only with relevant customer contacts",
            "severity": "High",
        },
    ]

    external_member = [
        {
            "file_name": "Design Assets (Shared Drive)",
            "owner_ou": "Marketing",
            "share_type": "external_member",
            "last_modified": "2026-03-20",
            "recommended_action": "Review external member access and remove accounts from outside approved vendor list",
            "severity": "Medium",
        },
        {
            "file_name": "Partner Integration Docs (Shared Drive)",
            "owner_ou": "Engineering",
            "share_type": "external_member",
            "last_modified": "2026-04-01",
            "recommended_action": "Audit external member list and enforce DLP policies on shared drive",
            "severity": "Medium",
        },
        {
            "file_name": "Customer POC Materials (Shared Drive)",
            "owner_ou": "Sales",
            "share_type": "external_member",
            "last_modified": "2026-04-10",
            "recommended_action": "Confirm active customer engagement and set expiration date for access",
            "severity": "Medium",
        },
    ]

    personal_gmail = [
        {
            "file_name": "Personal Backup - API Credentials.txt",
            "owner_ou": "Engineering",
            "share_type": "personal_gmail",
            "last_modified": "2025-07-19",
            "recommended_action": "Remove personal Gmail access immediately and rotate any exposed credentials",
            "severity": "High",
        },
        {
            "file_name": "Quarterly OKR Summary.docx",
            "owner_ou": "Executives",
            "share_type": "personal_gmail",
            "last_modified": "2025-11-05",
            "recommended_action": "Remove personal Gmail access and reshare via corporate account only",
            "severity": "High",
        },
    ]

    return anyone_with_link + external_member + personal_gmail


def _admin_roles() -> list:
    return [
        # 4 Super Admins (2 extra = Low finding)
        {
            "email": "olivia.chen@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-04-14",
            "ou": "IT/Admin",
            "flag_reason": "",
            "severity": "",
        },
        {
            "email": "marcus.reyes@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-04-12",
            "ou": "IT/Admin",
            "flag_reason": "",
            "severity": "",
        },
        {
            "email": "diana.foster@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-03-28",
            "ou": "IT/Admin",
            "flag_reason": "Super Admin count exceeds recommended maximum of 2",
            "severity": "Low",
        },
        {
            "email": "ryan.kim@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-04-08",
            "ou": "IT/Admin",
            "flag_reason": "Super Admin count exceeds recommended maximum of 2",
            "severity": "Low",
        },
        # 2 service accounts with Super Admin role (Critical)
        {
            "email": "svc-google-sync@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-04-13",
            "ou": "Service Accounts",
            "flag_reason": "Service account holds Super Admin role",
            "severity": "Critical",
        },
        {
            "email": "svc-directory-import@apexlabs.io",
            "role": "Super Admin",
            "last_login": "2026-03-30",
            "ou": "Service Accounts",
            "flag_reason": "Service account holds Super Admin role",
            "severity": "Critical",
        },
        # 7 delegated admins with no login in 90+ days (High)
        {
            "email": "alex.thornton@apexlabs.io",
            "role": "User Management Admin",
            "last_login": "2025-10-15",
            "ou": "Sales",
            "flag_reason": "No login in 182 days",
            "severity": "High",
        },
        {
            "email": "sarah.okonkwo@apexlabs.io",
            "role": "Groups Admin",
            "last_login": "2025-09-22",
            "ou": "Marketing",
            "flag_reason": "No login in 205 days",
            "severity": "High",
        },
        {
            "email": "james.wu@apexlabs.io",
            "role": "Helpdesk Admin",
            "last_login": "2025-11-10",
            "ou": "IT/Admin",
            "flag_reason": "No login in 156 days",
            "severity": "High",
        },
        {
            "email": "priya.sharma@apexlabs.io",
            "role": "User Management Admin",
            "last_login": "2025-08-30",
            "ou": "Finance",
            "flag_reason": "No login in 228 days",
            "severity": "High",
        },
        {
            "email": "tom.davidson@apexlabs.io",
            "role": "Reports Admin",
            "last_login": "2025-10-05",
            "ou": "Engineering",
            "flag_reason": "No login in 192 days",
            "severity": "High",
        },
        {
            "email": "lisa.carter@apexlabs.io",
            "role": "Helpdesk Admin",
            "last_login": "2025-12-20",
            "ou": "Customer Success",
            "flag_reason": "No login in 116 days",
            "severity": "High",
        },
        {
            "email": "mike.anderson@apexlabs.io",
            "role": "Groups Admin",
            "last_login": "2025-11-30",
            "ou": "Marketing",
            "flag_reason": "No login in 136 days",
            "severity": "High",
        },
    ]


def _mfa() -> dict:
    by_ou = [
        {"ou": "Engineering", "enrolled": 54, "total": 55, "pct": 98.2},
        {"ou": "Product", "enrolled": 21, "total": 22, "pct": 95.5},
        {"ou": "Sales", "enrolled": 32, "total": 41, "pct": 78.0},
        {"ou": "Marketing", "enrolled": 18, "total": 22, "pct": 81.8},
        {"ou": "Finance", "enrolled": 14, "total": 15, "pct": 93.3},
        {"ou": "Customer Success", "enrolled": 18, "total": 20, "pct": 90.0},
        {"ou": "IT/Admin", "enrolled": 15, "total": 15, "pct": 100.0},
        {"ou": "Executives", "enrolled": 5, "total": 5, "pct": 100.0},
        {"ou": "Legal/Compliance", "enrolled": 5, "total": 5, "pct": 100.0},
    ]

    total_users = sum(ou["total"] for ou in by_ou)
    enrolled_users = sum(ou["enrolled"] for ou in by_ou)
    overall_pct = round(enrolled_users / total_users * 100, 1)

    unenrolled_users = [
        # Sales (9 unenrolled)
        {"email": "derek.walsh@apexlabs.io", "ou": "Sales", "exception_documented": False},
        {"email": "nina.patel@apexlabs.io", "ou": "Sales", "exception_documented": False},
        {"email": "carlos.mendez@apexlabs.io", "ou": "Sales", "exception_documented": False},
        {"email": "tiffany.brooks@apexlabs.io", "ou": "Sales", "exception_documented": False},
        {"email": "jason.lee@apexlabs.io", "ou": "Sales", "exception_documented": False},
        {"email": "amy.grant@apexlabs.io", "ou": "Sales", "exception_documented": True},
        {"email": "brian.moore@apexlabs.io", "ou": "Sales", "exception_documented": True},
        {"email": "kelly.wright@apexlabs.io", "ou": "Sales", "exception_documented": True},
        {"email": "victor.huang@apexlabs.io", "ou": "Sales", "exception_documented": True},
        # Marketing (4 unenrolled)
        {"email": "rachel.nguyen@apexlabs.io", "ou": "Marketing", "exception_documented": False},
        {"email": "paul.simmons@apexlabs.io", "ou": "Marketing", "exception_documented": False},
        {"email": "anna.kowalski@apexlabs.io", "ou": "Marketing", "exception_documented": False},
        {"email": "chris.baker@apexlabs.io", "ou": "Marketing", "exception_documented": True},
        # Finance (1 unenrolled)
        {"email": "george.mwangi@apexlabs.io", "ou": "Finance", "exception_documented": False},
        # Customer Success (2 unenrolled)
        {"email": "hannah.scott@apexlabs.io", "ou": "Customer Success", "exception_documented": False},
        {"email": "ethan.jones@apexlabs.io", "ou": "Customer Success", "exception_documented": False},
        # Engineering (1 unenrolled)
        {"email": "lena.miller@apexlabs.io", "ou": "Engineering", "exception_documented": True},
        # Product (1 unenrolled)
        {"email": "omar.ali@apexlabs.io", "ou": "Product", "exception_documented": True},
    ]

    return {
        "overall_enrollment_pct": overall_pct,
        "threshold_pct": 95.0,
        "total_users": total_users,
        "enrolled_users": enrolled_users,
        "by_ou": by_ou,
        "unenrolled_users": unenrolled_users,
    }


def _dlp() -> dict:
    all_ous = [
        "Engineering", "Product", "Sales", "Marketing", "Finance",
        "Customer Success", "IT/Admin", "Executives", "Legal/Compliance",
    ]

    rules = [
        {
            "name": "Credit Card Pattern (PCI)",
            "pattern": "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\\b",
            "mode": "enforcing",
            "ous_covered": ["Engineering", "Finance", "Sales", "Customer Success", "IT/Admin", "Legal/Compliance"],
        },
        {
            "name": "SSN Pattern (PII)",
            "pattern": "\\b(?!000|666|9\\d{2})\\d{3}-(?!00)\\d{2}-(?!0000)\\d{4}\\b",
            "mode": "enforcing",
            "ous_covered": ["Finance", "IT/Admin", "Legal/Compliance", "Executives"],
        },
        {
            "name": "API Key / Token Detection",
            "pattern": "(?:api[_-]?key|token|secret)[\\s=:]+[\\w\\-]{20,}",
            "mode": "audit_only",
            "ous_covered": ["Engineering", "Product"],
        },
    ]

    covered_ous = set()
    for rule in rules:
        covered_ous.update(rule["ous_covered"])

    uncovered_ous = [
        {"ou": ou} for ou in all_ous if ou not in covered_ous
    ]

    audit_only_rules = [
        {
            "name": r["name"],
            "recommendation": "Switch enforcement mode from audit-only to block to prevent data exfiltration",
        }
        for r in rules
        if r["mode"] == "audit_only"
    ]

    return {
        "rules": rules,
        "all_ous": all_ous,
        "uncovered_ous": uncovered_ous,
        "audit_only_rules": audit_only_rules,
    }


def _vault() -> dict:
    all_ous = [
        "Engineering", "Product", "Sales", "Marketing", "Finance",
        "Customer Success", "IT/Admin", "Executives", "Legal/Compliance",
    ]

    rules = [
        {"ou": "Engineering", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Product", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Finance", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Finance", "service": "Drive", "retention_days": 2555, "explicit": True},
        {"ou": "Customer Success", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "IT/Admin", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Executives", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Executives", "service": "Drive", "retention_days": 2555, "explicit": True},
        {"ou": "Legal/Compliance", "service": "Gmail", "retention_days": 2555, "explicit": True},
        {"ou": "Legal/Compliance", "service": "Drive", "retention_days": 2555, "explicit": True},
    ]

    ous_with_rule = set(r["ou"] for r in rules)
    ous_without_rule = [ou for ou in all_ous if ou not in ous_with_rule]

    return {
        "rules": rules,
        "all_ous": all_ous,
        "ous_without_rule": ous_without_rule,
        "litigation_holds_count": 0,
    }


def _suspended_users() -> list:
    return [
        {"email": "former.cto@apexlabs.io", "group_memberships": 4, "drive_edit_access": 2},
        {"email": "ex.contractor.01@apexlabs.io", "group_memberships": 2, "drive_edit_access": 1},
        {"email": "ex.contractor.02@apexlabs.io", "group_memberships": 1, "drive_edit_access": 0},
        {"email": "intern.2024.summer@apexlabs.io", "group_memberships": 3, "drive_edit_access": 0},
        {"email": "onboarding.bot@apexlabs.io", "group_memberships": 5, "drive_edit_access": 0},
        {"email": "test.account.qa@apexlabs.io", "group_memberships": 1, "drive_edit_access": 0},
        {"email": "ex.sales.lead@apexlabs.io", "group_memberships": 2, "drive_edit_access": 0},
        {"email": "former.designer@apexlabs.io", "group_memberships": 1, "drive_edit_access": 0},
        {"email": "ex.devops.eng@apexlabs.io", "group_memberships": 0, "drive_edit_access": 0},
        {"email": "old.it.admin@apexlabs.io", "group_memberships": 0, "drive_edit_access": 0},
    ]
