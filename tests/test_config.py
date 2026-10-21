import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import main
class ConfigValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_file = Path(self.temp_dir.name) / "repo.json"
        self.repo_file.write_text('{"packages": []}', encoding="utf-8")
    def tearDown(self):
        self.temp_dir.cleanup()
    def parse(self, *extra):
        return main.main(
            ["--package", "demo-app", "--repository", str(self.repo_file), *extra]
        )
    def test_valid_local_configuration(self):
        args = main.build_parser().parse_args(
            [
                "--package", "demo-app",
                "--repository", str(self.repo_file),
                "--test-repo-mode", "local",
                "--max-depth", "2",
                "--filter", "demo",
            ]
        )
        config = main.validate_config(args)
        self.assertEqual(config.package_name, "demo-app")
        self.assertEqual(config.resolved_repo_mode, "local")
        self.assertEqual(config.max_depth, 2)
        self.assertEqual(config.package_filter, "demo")
    def test_missing_package_is_rejected(self):
        with self.assertRaises(SystemExit) as exc:
            main.main(["--repository", str(self.repo_file)])
        self.assertEqual(exc.exception.code, 2)
    def test_missing_repository_is_rejected(self):
        with self.assertRaises(SystemExit) as exc:
            main.main(["--package", "demo-app"])
        self.assertEqual(exc.exception.code, 2)
    def test_whitespace_package_validation(self):
        args = main.build_parser().parse_args(
            ["--package", "   ", "--repository", str(self.repo_file)]
        )
        with self.assertRaisesRegex(main.ConfigError, "--package"):
            main.validate_config(args)
    def test_unknown_repository_mode_is_rejected(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", str(self.repo_file), "--test-repo-mode", "bad"]
        )
        with self.assertRaisesRegex(main.ConfigError, "--test-repo-mode"):
            main.validate_config(args)
    def test_negative_depth_is_rejected_by_parser(self):
        with self.assertRaises(SystemExit) as exc:
            main.build_parser().parse_args(
                ["--package", "demo-app", "--repository", str(self.repo_file), "--max-depth", "-1"]
            )
        self.assertEqual(exc.exception.code, 2)
    def test_non_integer_depth_is_rejected_by_parser(self):
        with self.assertRaises(SystemExit) as exc:
            main.build_parser().parse_args(
                ["--package", "demo-app", "--repository", str(self.repo_file), "--max-depth", "many"]
            )
        self.assertEqual(exc.exception.code, 2)
    def test_blank_filter_is_rejected(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", str(self.repo_file), "--filter", "  "]
        )
        with self.assertRaisesRegex(main.ConfigError, "--filter"):
            main.validate_config(args)
    def test_missing_local_repository_is_rejected(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", str(Path(self.temp_dir.name) / "missing.json")]
        )
        with self.assertRaisesRegex(main.ConfigError, "не найден"):
            main.validate_config(args)
    def test_local_mode_rejects_url(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", "https://example.com/repo.json", "--test-repo-mode", "local"]
        )
        with self.assertRaisesRegex(main.ConfigError, "режима local"):
            main.validate_config(args)
    def test_remote_mode_rejects_path(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", str(self.repo_file), "--test-repo-mode", "remote"]
        )
        with self.assertRaisesRegex(main.ConfigError, "режима remote"):
            main.validate_config(args)
    def test_auto_mode_detects_remote_url(self):
        args = main.build_parser().parse_args(
            ["--package", "demo-app", "--repository", "https://example.com/repo.json"]
        )
        config = main.validate_config(args)
        self.assertEqual(config.resolved_repo_mode, "remote")
    def test_run_prints_key_value_parameters(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.parse("--test-repo-mode", "local", "--max-depth", "0")
        rendered = output.getvalue()
        self.assertIn("package=demo-app", rendered)
        self.assertIn("max_depth=0", rendered)
        self.assertIn("package_filter=(не задан)", rendered)
if __name__ == "__main__":
    unittest.main()