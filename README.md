# GWS Security Auditor

Audits a Google Workspace tenant across 6 security dimensions and produces a prioritized finding report.

---

## What It Finds

| Dimension | What Gets Checked |
|---|---|
| **External Sharing** | Drive files shared with "anyone with the link," external members, or personal Gmail accounts |
| **Admin Roles** | Super Admin count vs. recommended maximum, inactive delegated admins, service accounts with Super Admin |
| **MFA / 2SV** | 2-Step Verification enrollment by OU against a configurable threshold (default 95%) |
| **DLP Coverage** | DLP rule inventory, OUs with no rule coverage, rules running in audit-only mode |
| **Vault Retention** | Explicit retention rules per OU, OUs relying on default policy, litigation hold status |
| **Suspended Users** | Suspended accounts with active Google Group memberships or shared Drive edit access |

---

## Demo Mode

No credentials required. Demo runs against a synthetic 200-person org: **Apex Labs**, a Series B SaaS company with a realistic mix of passing and failing findings across all six dimensions.

Toggle between Demo and Live modes using the sidebar switch.

---

## Live Mode Setup

Live mode connects to the Google Admin SDK using a service account with domain-wide delegation.

### 1. Create a service account

In Google Cloud Console, create a service account and download the JSON key file.

### 2. Enable domain-wide delegation

In the Google Admin console (Security > API controls > Domain-wide delegation), add the service account with these OAuth scopes:

```
https://www.googleapis.com/auth/admin.directory.user.readonly
https://www.googleapis.com/auth/admin.directory.group.readonly
https://www.googleapis.com/auth/admin.reports.audit.readonly
https://www.googleapis.com/auth/apps.alerts
```

### 3. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:

```toml
[gws]
service_account_key_json = """{ ... paste full key JSON here ... }"""
admin_email = "admin@yourdomain.com"
domain = "yourdomain.com"
```

`secrets.toml` is excluded from version control by `.gitignore`.

---

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Stack

- **UI:** Streamlit
- **Charts:** Plotly
- **PDF Export:** fpdf2
- **GWS API:** Google Admin SDK (Directory + Reports API)

---

Built by [Oleg Strutsovski](https://linkedin.com/in/olegst) - IT Operations Manager
