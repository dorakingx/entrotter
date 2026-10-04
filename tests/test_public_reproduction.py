"""Fail-closed provenance controls; remote CI performs the actual public execution."""

from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/reproduce_clean.py"
REVISION = "a" * 40
URL = "https://github.com/dorakingx/entrotter.git"


class PublicReproductionTests(unittest.TestCase):
    def run_rejected(self, origin=URL, cloned_revision=REVISION, revision=REVISION):
        calls = []

        def output(command, **options):
            calls.append((command, options))
            if "diff" in command:
                return b""
            if "get-url" in command:
                return (
                    origin + "\n" if options.get("text") else (origin + "\n").encode()
                )
            if "rev-parse" in command:
                if command[-1] != "HEAD":
                    return (
                        "b" * 40 + "\n"
                        if options.get("text")
                        else ("b" * 40 + "\n").encode()
                    )
                value = (
                    revision
                    if str(SCRIPT.parent.parent) in command
                    else cloned_revision
                )
                return value + "\n" if options.get("text") else (value + "\n").encode()
            raise AssertionError("Unexpected command before provenance rejection")

        def run(command, **options):
            calls.append((command, options))
            if not command or command[0] != "git":
                raise AssertionError(
                    "A runtime/build command preceded provenance validation"
                )

        with (
            patch.object(sys, "argv", [str(SCRIPT), "--public", "--bounded"]),
            patch("subprocess.check_output", side_effect=output),
            patch("subprocess.run", side_effect=run),
        ):
            with self.assertRaises(ValueError) as error:
                runpy.run_path(str(SCRIPT), run_name="__main__")
        return str(error.exception), calls

    def test_wrong_public_origin_never_builds_or_falls_back(self):
        message, calls = self.run_rejected(origin="https://example.invalid/other.git")
        self.assertEqual(message, "Public clone origin changed")
        clones = [c for c, _ in calls if "clone" in c]
        self.assertEqual(len(clones), 1)
        self.assertIn(URL, clones[0])
        self.assertNotIn(str(SCRIPT.parent.parent), clones[0])

    def test_wrong_revision_never_executes_cloned_code(self):
        message, _ = self.run_rejected(cloned_revision="c" * 40)
        self.assertEqual(message, "Source revision changed during clone")

    def test_inherited_git_config_cannot_redirect_or_authorize_the_clone(self):
        with patch.dict(
            "os.environ",
            {
                "GIT_DIR": "/private/foreign-store",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.extraHeader",
                "GIT_CONFIG_VALUE_0": "PRIVATE_TEST_HEADER",
            },
        ):
            _, calls = self.run_rejected(origin="https://example.invalid/other.git")
        for command, options in calls:
            env = options["env"]
            for key in [
                "GIT_DIR",
                "GIT_CONFIG_COUNT",
                "GIT_CONFIG_KEY_0",
                "GIT_CONFIG_VALUE_0",
            ]:
                self.assertNotIn(key, env)
            self.assertEqual(env["GIT_CONFIG_GLOBAL"], "/dev/null")
            self.assertEqual(env["GIT_CONFIG_NOSYSTEM"], "1")
            self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
            self.assertNotIn("shell", options)
            if "clone" in command:
                self.assertIn("credential.helper=", command)
                self.assertIn("http.extraHeader=", command)
                self.assertIn("http.cookieFile=", command)


if __name__ == "__main__":
    unittest.main()
