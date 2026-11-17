import json
import tempfile
import unittest
from pathlib import Path

from src.dependency_graph import GraphError, load_test_repository


class TestRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.temp_dir.name) / "repo.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def write_repository(self, packages: list[dict]) -> None:
        payload = {"repository_name": "test", "packages": packages}
        self.file_path.write_text(
            json.dumps(payload),
            encoding="utf-8",
        )

    def test_loads_uppercase_package_names(self) -> None:
        self.write_repository(
            [
                {"name": "A", "dependencies": ["B"]},
                {"name": "B", "dependencies": []},
            ]
        )
        self.assertEqual(
            load_test_repository(self.file_path),
            {"A": ["B"], "B": []},
        )

    def test_rejects_lowercase_package_name(self) -> None:
        self.write_repository([{"name": "alpha", "dependencies": []}])
        with self.assertRaisesRegex(GraphError, "A-Z"):
            load_test_repository(self.file_path)

    def test_rejects_unknown_dependency(self) -> None:
        self.write_repository(
            [{"name": "A", "dependencies": ["B"]}]
        )
        with self.assertRaisesRegex(GraphError, "отсутствующего"):
            load_test_repository(self.file_path)

    def test_rejects_duplicate_package(self) -> None:
        self.write_repository(
            [
                {"name": "A", "dependencies": []},
                {"name": "A", "dependencies": []},
            ]
        )
        with self.assertRaisesRegex(GraphError, "более одного раза"):
            load_test_repository(self.file_path)

    def test_rejects_invalid_json(self) -> None:
        self.file_path.write_text("{bad json", encoding="utf-8")
        with self.assertRaisesRegex(GraphError, "Некорректный JSON"):
            load_test_repository(self.file_path)


if __name__ == "__main__":
    unittest.main()
