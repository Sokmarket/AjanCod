import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from aegis.agent import AgentError, _safe_relative_target, collect_context, run_agent


class AgentSafetyTests(unittest.TestCase):
    def test_context_redacts_common_inline_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "settings.toml").write_text('api_key = "sk-abcdefghijklmnopqrstuvwxyz123456"\npassword = hunter2\n', encoding="utf-8")
            context = collect_context(root)
            self.assertNotIn("abcdefghijklmnopqrstuvwxyz123456", context)
            self.assertNotIn("hunter2", context)
            self.assertIn("[REDACTED]", context)

    def test_context_skips_sensitive_file_names(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "service-token.txt").write_text("token-material", encoding="utf-8")
            (root / "main.py").write_text("print('ok')", encoding="utf-8")
            context = collect_context(root)
            self.assertNotIn("token-material", context)
            self.assertIn("main.py", context)

    def test_model_target_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            with self.assertRaises(AgentError):
                _safe_relative_target(root, "../outside.py")
            with self.assertRaises(AgentError):
                _safe_relative_target(root, ".aegis/state.json")

    def test_proposal_mode_does_not_write_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "main.py").write_text("value = 1\n", encoding="utf-8")
            proposal = {"summary": "Set value to two", "files": [{"path": "main.py", "content": "value = 2\n"}]}
            with patch("aegis.agent._chat_completion", return_value=proposal):
                result = run_agent(root, "change value", apply_changes=False)
            self.assertEqual(result["status"], "PROPOSED")
            self.assertEqual((root / "main.py").read_text(encoding="utf-8"), "value = 1\n")
            self.assertTrue((root / "reports/agent-proposal.json").is_file())
            self.assertIn("-value = 1", result["diffs"][0]["diff"])

    def test_apply_creates_backup_before_replacing_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "main.py"
            target.write_text("value = 1\n", encoding="utf-8")
            proposal = {"summary": "Set value to two", "files": [{"path": "main.py", "content": "value = 2\n"}]}
            with patch("aegis.agent._chat_completion", return_value=proposal):
                result = run_agent(root, "change value", apply_changes=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "value = 2\n")
            self.assertIsNotNone(result["backup_directory"])
            backup = Path(result["backup_directory"]) / "main.py"
            self.assertEqual(backup.read_text(encoding="utf-8"), "value = 1\n")

    def test_rejects_invalid_proposal_before_any_source_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            target = root / "main.py"
            target.write_text("old = True\n", encoding="utf-8")
            proposal = {"summary": "bad path", "files": [
                {"path": "main.py", "content": "new = True\n"},
                {"path": "../escape.py", "content": "bad = True\n"},
            ]}
            with patch("aegis.agent._chat_completion", return_value=proposal):
                with self.assertRaises(AgentError):
                    run_agent(root, "malformed", apply_changes=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "old = True\n")



class AgentRollbackTests(unittest.TestCase):
    def test_failed_second_write_restores_first_target(self):
        import aegis.agent as agent_module
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "first.py").write_text("old_first = True\n", encoding="utf-8")
            (root / "second.py").write_text("old_second = True\n", encoding="utf-8")
            proposal = {"summary": "change both", "files": [
                {"path": "first.py", "content": "new_first = True\n"},
                {"path": "second.py", "content": "new_second = True\n"},
            ]}
            real_write = agent_module._atomic_write
            calls = {"count": 0}
            def flaky_write(path, content):
                calls["count"] += 1
                if calls["count"] == 2:
                    raise OSError("simulated storage failure")
                return real_write(path, content)
            with patch("aegis.agent._chat_completion", return_value=proposal), patch("aegis.agent._atomic_write", side_effect=flaky_write):
                with self.assertRaises(AgentError):
                    run_agent(root, "change both", apply_changes=True)
            self.assertEqual((root / "first.py").read_text(encoding="utf-8"), "old_first = True\n")
            self.assertEqual((root / "second.py").read_text(encoding="utf-8"), "old_second = True\n")


class EndpointPolicyTests(unittest.TestCase):
    def test_plain_http_remote_endpoint_is_rejected(self):
        from aegis.agent import _endpoint_config
        with patch.dict("os.environ", {"AEGIS_API_BASE": "http://example.com/v1", "AEGIS_MODEL": "test-model"}, clear=False):
            with self.assertRaises(AgentError):
                _endpoint_config()

    def test_https_remote_endpoint_is_accepted_without_contacting_it(self):
        from aegis.agent import _endpoint_config
        with patch.dict("os.environ", {"AEGIS_API_BASE": "https://example.com/v1", "AEGIS_MODEL": "test-model"}, clear=False):
            base, model, _key = _endpoint_config()
        self.assertEqual(base, "https://example.com/v1")
        self.assertEqual(model, "test-model")

class SourceRedactionTests(unittest.TestCase):
    def test_context_redaction_does_not_damage_environment_lookup_code(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            code = 'api_key = os.environ.get("AEGIS_API_KEY")\ntoken = get_token()\n'
            (root / "main.py").write_text(code, encoding="utf-8")
            context = collect_context(root)
            self.assertIn('api_key = os.environ.get("AEGIS_API_KEY")', context)
            self.assertIn('token = get_token()', context)

class RedirectPolicyTests(unittest.TestCase):
    def test_api_redirects_are_not_followed(self):
        from aegis.agent import _NoRedirect
        from urllib.request import Request
        blocker = _NoRedirect()
        request = Request("https://example.com/v1/chat/completions", data=b"{}", method="POST")
        self.assertIsNone(blocker.redirect_request(request, None, 307, "Temporary Redirect", {}, "https://elsewhere.example/collect"))
if __name__ == "__main__":
    unittest.main()
