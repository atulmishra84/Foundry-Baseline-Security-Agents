import unittest
from unittest.mock import patch

from tools.prod.entra_containment import execute_approved_containment, set_service_principal_enabled


class EntraContainmentTests(unittest.TestCase):
    @patch("tools.prod.entra_containment.allowed_sp_id", return_value="sp-allowed")
    def test_refuses_other_object_id(self, _allowed):
        with self.assertRaises(PermissionError):
            set_service_principal_enabled("sp-other", False, token="t")

    @patch("tools.prod.entra_containment.allowed_sp_id", return_value="sp-allowed")
    @patch("tools.prod.entra_containment.requests.patch")
    def test_patches_allowlisted_sp(self, patch_req, _allowed):
        patch_req.return_value.status_code = 204
        result = set_service_principal_enabled("sp-allowed", False, token="t")
        self.assertEqual(result["accountEnabled"], False)
        self.assertIn("servicePrincipals/sp-allowed", patch_req.call_args.args[0])

    @patch("tools.prod.entra_containment.allowed_sp_id", return_value="")
    def test_execute_without_config(self, _allowed):
        incident = execute_approved_containment({"incident_id": "INC-1"})
        self.assertFalse(incident["containment"]["executed"])
        self.assertIn("containment_service_principal_id", incident["containment"]["reason"])


if __name__ == "__main__":
    unittest.main()
