"""
Access control for live mode.

Live mode impersonates a Workspace super admin through domain-wide delegation
and returns every user, admin role, 2-Step Verification state and sharing
event in the tenant. That is for the operator only. A visitor who has not
signed in gets Demo Mode, which runs on synthetic data.

Identity comes only from Streamlit's OIDC sign-in (st.login / st.user), and the
signed-in address must be on the `allowed_emails` list in the deployment's
secrets. Nothing typed or toggled in the page can grant live access.
"""

import os

import streamlit as st

# Local use only: see _dev_login_email().
_DEV_LOGIN_ENV = "GWS_AUDITOR_DEV_LOGIN_EMAIL"
_LOOPBACK_ADDRESSES = {"localhost", "127.0.0.1", "::1"}


def _is_email(value) -> bool:
    return isinstance(value, str) and "@" in value


def _claim(user, name, default=None):
    """Read one attribute of st.user. Never raises."""
    try:
        return getattr(user, name)
    except Exception:
        return default


def _verified_email():
    """Email of a user who completed the identity provider's sign-in, or None."""
    user = getattr(st, "user", None)
    if user is None:
        # Name used by the first Streamlit releases that had st.login.
        user = getattr(st, "experimental_user", None)
    if user is None:
        return None
    if _claim(user, "is_logged_in") is not True:
        return None
    email = _claim(user, "email")
    if not _is_email(email):
        return None
    # Providers that report whether the address was verified must say yes.
    if _claim(user, "email_verified", True) is False:
        return None
    return email


def _allowed_emails() -> set:
    """Lower-cased `allowed_emails` secret. Missing or unusable means nobody."""
    try:
        raw = st.secrets.get("allowed_emails", None)
    except Exception:
        return set()
    if isinstance(raw, str):
        raw = [raw]
    try:
        return {x.strip().lower() for x in raw if isinstance(x, str) and x.strip()}
    except Exception:
        return set()


def _server_is_loopback_only() -> bool:
    """True only when Streamlit is bound to this machine's loopback interface."""
    try:
        address = st.get_option("server.address")
    except Exception:
        return False
    return isinstance(address, str) and address.strip().lower() in _LOOPBACK_ADDRESSES


def _dev_login_email():
    """Operator identity for a server that only this machine can reach, or None.

    Needs both GWS_AUDITOR_DEV_LOGIN_EMAIL and a loopback-only server
    (`streamlit run app.py --server.address localhost`). A deployed app listens
    on a routable address, so setting the variable there changes nothing.
    """
    email = os.environ.get(_DEV_LOGIN_ENV, "").strip()
    if not _is_email(email):
        return None
    if not _server_is_loopback_only():
        return None
    return email


def current_user():
    """Email of the user allowed to run a live audit, or None."""
    email = _verified_email()
    if email is not None:
        return email if email.strip().lower() in _allowed_emails() else None
    return _dev_login_email()


def live_access_allowed() -> bool:
    """True when this session may audit the real tenant."""
    return current_user() is not None


def require_live_access() -> None:
    """Raise unless this session may audit the real tenant."""
    if not live_access_allowed():
        raise PermissionError("Live mode requires a signed-in user on the allowed_emails list.")


def render_sign_in(key: str = "sign_in") -> None:
    """Offer the identity provider's sign-in, or say why access was refused."""
    if _verified_email() is not None:
        st.error("Your account is not on this deployment's allow list for live mode.")
        logout = getattr(st, "logout", None)
        if logout is not None and st.button("Sign out", key=f"{key}_out"):
            try:
                logout()
            except Exception:
                pass
        return

    if os.environ.get(_DEV_LOGIN_ENV, "").strip() and not _server_is_loopback_only():
        st.warning(
            f"{_DEV_LOGIN_ENV} is set but ignored: it only works when the server is "
            "bound to this machine (`streamlit run app.py --server.address localhost`)."
        )

    login = getattr(st, "login", None)
    if login is None:
        st.error("This Streamlit version has no sign-in support; install the pinned requirements.")
        return
    if st.button("Sign in for live mode", key=f"{key}_in"):
        try:
            login()
        except Exception:
            st.error(
                "Sign-in is not configured for this deployment. Add an [auth] section and "
                "`allowed_emails` to its secrets (see .streamlit/secrets.toml.example)."
            )
