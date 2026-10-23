import unittest

from server.auth.jwt import resolve_user_role


class AdminPanelTests(unittest.TestCase):
    def test_admin_role_is_detected_from_configured_admin_email(self):
        self.assertEqual(resolve_user_role("admin@example.com"), "admin")

    def test_user_role_is_default_for_non_admin_email(self):
        self.assertEqual(resolve_user_role("player@example.com"), "user")


if __name__ == "__main__":
    unittest.main()
