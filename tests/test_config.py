import contextlib
import io
import tempfile
import unittest
from pathlib import Path
import main
class ConfigValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_file = Path(self.temp_dir.name) / "repo.json"
        self.repo_file.write_text('{"packages": []}', encoding="utf-8")
    def tearDown(self) -> None:
        self.temp_dir.cleanup()
    def parse(self, *extra: str) -> int:
        argv = [
            "--package",
            "demo-app",
            "--repository",
            str(self.repo_file),
            *extra,
        ]
        return main.main(argv)
    def _parse_args(self, *extra: str):
        argv = [
            "--package",
            "demo-app",
            "--repository",
            str(self.repo_file),
            *extra,
        ]
        return main.build_parser().parse_args(argv)
    def test_valid_local_configuration(self) -> None:
        args = self._parse_args(
            "--test-repo-mode",
            "local",
            "--max-depth",
            "2",
            "--filter",
            "demo",
        )
        config = main.validate_config(args)
        self.assertEqual(config.package_name, "demo-app")
        self.assertEqual(config.resolved_repo_mode, "local")
        self.assertEqual(config.max_depth, 2)
        self.assertEqual(config.package_filter, "demo")
    def test_missing_package_is_rejected(self) -> None:
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            result = main.main(["--repository", str(self.repo_file)])
        self.assertEqual(result, 2)
        self.assertIn("--package", errors.getvalue())
    def test_missing_repository_is_rejected(self) -> None:
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            result = main.main(["--package", "demo-app"])
        self.assertEqual(result, 2)
        self.assertIn("--repository", errors.getvalue())
    def test_whitespace_package_validation(self) -> None:
        args = self._parse_args()
        args.package = "   "
        with self.assertRaisesRegex(main.ConfigError, "--package"):
            main.validate_config(args)
    def test_unknown_repository_mode_is_rejected(self) -> None:
        args = self._parse_args("--test-repo-mode", "bad")
        with self.assertRaisesRegex(main.ConfigError, "--test-repo-mode"):
            main.validate_config(args)
    def test_negative_depth_is_rejected_by_parser(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self._parse_args("--max-depth", "-1")
        self.assertEqual(exc.exception.code, 2)
    def test_non_integer_depth_is_rejected_by_parser(self) -> None:
        with self.assertRaises(SystemExit) as exc:
            self._parse_args("--max-depth", "many")
        self.assertEqual(exc.exception.code, 2)
    def test_blank_filter_is_rejected(self) -> None:
        args = self._parse_args("--filter", "  ")
        with self.assertRaisesRegex(main.ConfigError, "--filter"):
            main.validate_config(args)
    def test_missing_local_repository_is_rejected(self) -> None:
        missing = Path(self.temp_dir.name) / "missing.json"
        args = self._parse_args("--repository", str(missing))
        with self.assertRaisesRegex(main.ConfigError, "не найден"):
            main.validate_config(args)
    def test_local_mode_rejects_url(self) -> None:
        args = self._parse_args(
            "--repository",
            "https://example.com/repo.json",
            "--test-repo-mode",
            "local",
        )
        with self.assertRaisesRegex(main.ConfigError, "режима local"):
            main.validate_config(args)
    def test_remote_mode_rejects_path(self) -> None:
        args = self._parse_args("--test-repo-mode", "remote")
        with self.assertRaisesRegex(main.ConfigError, "режима remote"):
            main.validate_config(args)
    def test_invalid_http_url_is_rejected(self) -> None:
        args = self._parse_args("--repository", "http://[bad")
        with self.assertRaisesRegex(main.ConfigError, "некорректный URL"):
            main.validate_config(args)
    def test_directory_repository_is_rejected(self) -> None:
        args = self._parse_args("--repository", self.temp_dir.name)
        with self.assertRaisesRegex(main.ConfigError, "каталог"):
            main.validate_config(args)
    def test_auto_mode_detects_remote_url(self) -> None:
        args = self._parse_args(
            "--repository",
            "https://example.com/repo.json",
        )
        config = main.validate_config(args)
        self.assertEqual(config.resolved_repo_mode, "remote")
    def test_run_prints_key_value_parameters(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.parse("--test-repo-mode", "local", "--max-depth", "0")
        rendered = output.getvalue()
        self.assertIn("package=demo-app", rendered)
        self.assertIn("max_depth=0", rendered)
        self.assertIn("package_filter=(не задан)", rendered)
if __name__ == "__main__":
    unittest.main()