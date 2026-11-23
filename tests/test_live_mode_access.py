"""Live mode must be out of reach without a signed-in, allow-listed user."""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import auth  # noqa: E402
from connectors import gws_connector  # noqa: E402

GWS_SECRETS = {
    "admin_email": "admin@example.org",
    "domain": "example.org",
    "service_account_key_json": '{"type": "service_account"}',
}


class _User:
    def __init__(self, **claims):
        self._claims = claims

    def __getattr__(self, name):
        try:
            return self.__dict__["_claims"][name]
        except KeyError:
            raise AttributeError(name) from None


class _FakeStreamlit:
    def __init__(self, user=None, secrets=None, address=None, session_state=None):
        self.user = user if user is not None else _User()
        self.secrets = {"gws": dict(GWS_SECRETS)}
        self.secrets.update(secrets or {})
        self._address = address
        self.session_state = session_state or {}

    def get_option(self, name):
        assert name == "server.address"
        return self._address


def _patched(fake, env=None):
    environ = {k: v for k, v in os.environ.items() if k != auth._DEV_LOGIN_ENV}
    environ.update(env or {})
    return mock.patch.object(auth, "st", fake), mock.patch.dict(os.environ, environ, clear=True)


def _signed_in(email="pat@example.org", **claims):
    return _User(is_logged_in=True, email=email, **claims)


class LiveAccessTests(unittest.TestCase):
    def _user(self, fake, env=None):
        p1, p2 = _patched(fake, env)
        with p1, p2:
            return auth.current_user()

    def test_anonymous_session_has_no_live_access(self):
        self.assertIsNone(self._user(_FakeStreamlit()))

    def test_session_state_cannot_grant_live_access(self):
        fake = _FakeStreamlit(session_state={"demo_mode": False, "current_user": "pat@example.org"})
        self.assertIsNone(self._user(fake))

    def test_signed_in_and_allow_listed_user_has_live_access(self):
        fake = _FakeStreamlit(user=_signed_in("Pat@Example.org"), secrets={"allowed_emails": ["pat@example.org"]})
        self.assertEqual(self._user(fake), "Pat@Example.org")

    def test_signed_in_user_off_the_list_has_none(self):
        for allowed in (None, [], ["lee@example.org"], 7, ""):
            fake = _FakeStreamlit(user=_signed_in(), secrets={"allowed_emails": allowed})
            self.assertIsNone(self._user(fake), allowed)

    def test_an_address_without_a_completed_sign_in_is_not_an_identity(self):
        allow = {"allowed_emails": ["pat@example.org"]}
        for user in (
            _User(email="pat@example.org"),
            _User(is_logged_in=False, email="pat@example.org"),
            _User(is_logged_in="true", email="pat@example.org"),
            _User(is_logged_in=True),
            _User(is_logged_in=True, email="pat@example.org", email_verified=False),
        ):
            self.assertIsNone(self._user(_FakeStreamlit(user=user, secrets=allow)))

    def test_dev_login_needs_the_variable_and_a_loopback_only_server(self):
        env = {auth._DEV_LOGIN_ENV: "dev@example.org"}
        self.assertEqual(self._user(_FakeStreamlit(address="localhost"), env), "dev@example.org")
        for address in (None, "", "0.0.0.0", "10.0.0.5"):
            self.assertIsNone(self._user(_FakeStreamlit(address=address), env), address)
        self.assertIsNone(self._user(_FakeStreamlit(address="localhost")))


class ConnectorGuardTests(unittest.TestCase):
    def test_connector_refuses_to_build_credentials_without_live_access(self):
        fake = _FakeStreamlit()
        p1, p2 = _patched(fake)
        with p1, p2, mock.patch.object(gws_connector, "st", fake), \
                mock.patch.object(gws_connector, "service_account", create=True) as sa, \
                mock.patch.object(gws_connector, "build", create=True) as build:
            with self.assertRaises(PermissionError):
                gws_connector.load_all()
            with self.assertRaises(PermissionError):
                gws_connector._build_credentials()
            sa.Credentials.from_service_account_info.assert_not_called()
            build.assert_not_called()

    def test_connector_builds_credentials_for_an_allowed_user(self):
        fake = _FakeStreamlit(user=_signed_in(), secrets={"allowed_emails": ["pat@example.org"]})
        p1, p2 = _patched(fake)
        with p1, p2, mock.patch.object(gws_connector, "st", fake), \
                mock.patch.object(gws_connector, "GCP_AVAILABLE", True), \
                mock.patch.object(gws_connector, "service_account", create=True) as sa:
            _, domain = gws_connector._build_credentials()
        self.assertEqual(domain, "example.org")
        sa.Credentials.from_service_account_info.assert_called_once()


class RealStreamlitTests(unittest.TestCase):
    """Run the real pages under Streamlit's test harness with live secrets configured."""

    def setUp(self):
        try:
            from streamlit.testing.v1 import AppTest
        except Exception:  # pragma: no cover - older Streamlit
            self.skipTest("streamlit.testing is not available")
        self.AppTest = AppTest
        environ = {k: v for k, v in os.environ.items() if k != auth._DEV_LOGIN_ENV}
        patcher = mock.patch.dict(os.environ, environ, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

        def _no_live_call(*args, **kwargs):
            raise AssertionError("the live connector must not be reached")

        for name in ("_fetch_users", "_fetch_groups"):
            p = mock.patch.object(gws_connector, name, side_effect=_no_live_call)
            p.start()
            self.addCleanup(p.stop)

    def _app(self, script, **session_state):
        at = self.AppTest.from_file(str(ROOT / script), default_timeout=120)
        at.secrets["gws"] = dict(GWS_SECRETS)
        for key, value in session_state.items():
            at.session_state[key] = value
        return at.run()

    def test_anonymous_visitor_gets_demo_data_and_no_live_switch(self):
        at = self._app("app.py")
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(len(at.toggle), 0)
        self.assertEqual([b.label for b in at.sidebar.button], ["Sign in for live mode"])
        self.assertEqual(at.session_state["data"]["org_name"], "Apex Labs")

    def test_a_session_claiming_live_mode_is_put_back_on_demo_data(self):
        for script in ("app.py", "pages/3_Admin_Roles.py", "pages/4_MFA_Enforcement.py"):
            at = self._app(script, demo_mode=False)
            self.assertFalse(at.exception, (script, [e.value for e in at.exception]))
            self.assertIs(at.session_state["demo_mode"], True, script)
            self.assertEqual(at.session_state["data"]["org_name"], "Apex Labs", script)

    def test_live_data_already_in_the_session_is_dropped(self):
        at = self._app("app.py", demo_mode=False, data={"org_name": "example.org", "admin_roles": []},
                       findings=[], scores={"overall": 0, "by_category": {}})
        self.assertFalse(at.exception, [e.value for e in at.exception])
        self.assertEqual(at.session_state["data"]["org_name"], "Apex Labs")


if __name__ == "__main__":
    unittest.main()
