"""
Live Google Workspace connector using the Admin SDK.
Returns data in the same shape as demo_data.load_all().

Requires a service account with domain-wide delegation configured.
Set credentials in .streamlit/secrets.toml (see secrets.toml.example).
"""

import json
import streamlit as st
from datetime import datetime, timezone, timedelta

try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
    "https://www.googleapis.com/auth/admin.reports.audit.readonly",
    "https://www.googleapis.com/auth/apps.alerts",
]


def _build_credentials():
    if not GCP_AVAILABLE:
        raise RuntimeError(
            "Google API libraries not installed. Run: pip install google-api-python-client google-auth google-auth-httplib2"
        )

    gws_cfg = st.secrets.get("gws", {})
    admin_email = gws_cfg.get("admin_email", "")
    domain = gws_cfg.get("domain", "")

    if not admin_email or not domain:
        raise ValueError(
            "Missing 'admin_email' or 'domain' in [gws] section of secrets.toml"
        )

    key_json = gws_cfg.get("service_account_key_json", "")
    key_path = gws_cfg.get("service_account_key_path", "")

    if key_json:
        info = json.loads(key_json)
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    elif key_path:
        creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    else:
        raise ValueError(
            "Provide 'service_account_key_json' or 'service_account_key_path' in secrets.toml"
        )

    return creds.with_subject(admin_email), domain


def load_all() -> dict:
    creds, domain = _build_credentials()

    directory = build("admin", "directory_v1", credentials=creds)
    reports = build("admin", "reports_v1", credentials=creds)

    users = _fetch_users(directory, domain)
    groups = _fetch_groups(directory, domain)

    return {
        "org_name": domain,
        "total_users": len([u for u in users if not u.get("suspended", False)]),
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "external_sharing": _fetch_external_sharing(reports),
        "admin_roles": _fetch_admin_roles(directory, domain, users),
        "mfa": _fetch_mfa(directory, users),
        "dlp": _fetch_dlp(),
        "vault": _fetch_vault(),
        "suspended_users": _fetch_suspended_users(directory, users, groups),
    }


def _fetch_users(directory, domain) -> list:
    users = []
    page_token = None
    while True:
        resp = directory.users().list(
            domain=domain,
            maxResults=500,
            pageToken=page_token,
            projection="full",
        ).execute()
        users.extend(resp.get("users", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return users


def _fetch_groups(directory, domain) -> list:
    groups = []
    page_token = None
    while True:
        resp = directory.groups().list(
            domain=domain,
            maxResults=200,
            pageToken=page_token,
        ).execute()
        groups.extend(resp.get("groups", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return groups


def _fetch_external_sharing(reports) -> list:
    """
    Pulls Drive sharing activity from the Reports API.
    Returns records matching the demo_data shape.
    """
    results = []
    try:
        resp = reports.activities().list(
            userKey="all",
            applicationName="drive",
            eventName="change_acl_editors",
            maxResults=500,
        ).execute()
        for activity in resp.get("items", []):
            for event in activity.get("events", []):
                params = {p["name"]: p.get("value", "") for p in event.get("parameters", [])}
                visibility = params.get("visibility", "")
                if visibility in ("people_with_link", "public_on_the_web"):
                    results.append({
                        "file_name": params.get("doc_title", "Unknown"),
                        "owner_ou": params.get("owner", "Unknown"),
                        "share_type": "anyone_with_link",
                        "last_modified": activity.get("id", {}).get("time", "")[:10],
                        "recommended_action": "Remove public link and restrict to domain users only",
                        "severity": "High",
                    })
    except Exception as exc:
        st.error(f"Error fetching Drive sharing activity: {exc}")
    return results


def _fetch_admin_roles(directory, domain, users) -> list:
    results = []
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()

    try:
        roles_resp = directory.roles().list(customer="my_customer").execute()
        role_map = {r["roleId"]: r["roleName"] for r in roles_resp.get("items", [])}

        assignments_resp = directory.roleAssignments().list(customer="my_customer").execute()
        user_map = {u["id"]: u for u in users}

        for assignment in assignments_resp.get("items", []):
            user_id = assignment.get("assignedTo", "")
            user = user_map.get(user_id, {})
            email = user.get("primaryEmail", user_id)
            role_name = role_map.get(assignment.get("roleId", ""), "Unknown Role")

            ou = user.get("orgUnitPath", "/").lstrip("/") or "Root"
            last_login = user.get("lastLoginTime", "")[:10] or "Never"
            is_service = user.get("isServiceAccount", False)

            flag_reason = ""
            severity = ""
            if is_service and "Super Admin" in role_name:
                flag_reason = "Service account holds Super Admin role"
                severity = "Critical"
            elif last_login != "Never" and last_login < cutoff[:10]:
                days = (datetime.now() - datetime.fromisoformat(last_login)).days
                flag_reason = f"No login in {days} days"
                severity = "High"

            results.append({
                "email": email,
                "role": role_name,
                "last_login": last_login,
                "ou": ou,
                "flag_reason": flag_reason,
                "severity": severity,
            })
    except Exception as exc:
        st.error(f"Error fetching admin roles: {exc}")

    return results


def _fetch_mfa(directory, users) -> dict:
    by_ou: dict[str, dict] = {}

    for user in users:
        if user.get("suspended", False):
            continue
        ou = user.get("orgUnitPath", "/").lstrip("/").split("/")[0] or "Root"
        if ou not in by_ou:
            by_ou[ou] = {"ou": ou, "enrolled": 0, "total": 0}
        by_ou[ou]["total"] += 1
        if user.get("isEnrolledIn2Sv", False):
            by_ou[ou]["enrolled"] += 1

    ou_list = []
    for entry in by_ou.values():
        entry["pct"] = round(entry["enrolled"] / entry["total"] * 100, 1) if entry["total"] > 0 else 0.0
        ou_list.append(entry)

    total_users = sum(e["total"] for e in ou_list)
    enrolled_users = sum(e["enrolled"] for e in ou_list)
    overall_pct = round(enrolled_users / total_users * 100, 1) if total_users > 0 else 0.0

    unenrolled_users = [
        {
            "email": u["primaryEmail"],
            "ou": u.get("orgUnitPath", "/").lstrip("/").split("/")[0] or "Root",
            "exception_documented": False,
        }
        for u in users
        if not u.get("suspended", False) and not u.get("isEnrolledIn2Sv", False)
    ]

    return {
        "overall_enrollment_pct": overall_pct,
        "threshold_pct": 95.0,
        "total_users": total_users,
        "enrolled_users": enrolled_users,
        "by_ou": ou_list,
        "unenrolled_users": unenrolled_users,
    }


def _fetch_dlp() -> dict:
    """
    DLP rules are managed via the Google Admin console and are not directly
    accessible through the standard Admin SDK in all configurations.
    This returns an empty scaffold. Populate manually or extend with
    the Chrome Management or Alert Center APIs.
    """
    return {
        "rules": [],
        "all_ous": [],
        "uncovered_ous": [],
        "audit_only_rules": [],
    }


def _fetch_vault() -> dict:
    """
    Vault retention rules require the Vault API (vault.googleapis.com).
    The service account must have the Vault Operator or Vault Admin role.
    Extend this function using the Google Vault Python client library.
    """
    return {
        "rules": [],
        "all_ous": [],
        "ous_without_rule": [],
        "litigation_holds_count": 0,
    }


def _fetch_suspended_users(directory, users, groups) -> list:
    suspended = [u for u in users if u.get("suspended", False)]
    results = []

    group_members_cache: dict[str, set] = {}

    for user in suspended:
        email = user.get("primaryEmail", "")
        memberships = 0
        try:
            resp = directory.groups().list(
                userKey=email,
                maxResults=200,
            ).execute()
            memberships = len(resp.get("groups", []))
        except Exception:
            pass

        results.append({
            "email": email,
            "group_memberships": memberships,
            "drive_edit_access": 0,  # Drive API required for full check
        })

    return results
