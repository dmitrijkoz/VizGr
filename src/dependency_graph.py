from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

PACKAGE_NAME_PATTERN = re.compile(r"^[A-Z]+$")


class GraphError(ValueError):
    """Ошибка структуры репозитория или построения графа."""


def _validate_package_name(name: object, context: str) -> str:
    if not isinstance(name, str) or not PACKAGE_NAME_PATTERN.fullmatch(name):
        raise GraphError(
            f"{context}: имя пакета должно состоять из больших "
            "латинских букв A-Z."
        )
    return name


def load_test_repository(file_path: str | Path) -> dict[str, list[str]]:
    """Загружает тестовый граф из JSON и проверяет его структуру."""
    path = Path(file_path)
    try:
        raw_text = path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except OSError as exc:
        raise GraphError(
            f"Не удалось прочитать тестовый репозиторий: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise GraphError(
            f"Некорректный JSON тестового репозитория: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise GraphError("Корень файла репозитория должен быть объектом.")
    packages = data.get("packages")
    if not isinstance(packages, list):
        raise GraphError("В тестовом репозитории нужен список packages.")
    graph: dict[str, list[str]] = {}
    for index, item in enumerate(packages):
        if not isinstance(item, dict):
            raise GraphError(f"Элемент packages[{index}] должен быть объектом.")
        name = _validate_package_name(
            item.get("name"), f"packages[{index}]"
        )
        if name in graph:
            raise GraphError(f"Пакет {name} указан более одного раза.")
        dependencies = item.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise GraphError(f"Список dependencies пакета {name} неверен.")
        checked_dependencies = [
            _validate_package_name(dep, f"Зависимость пакета {name}")
            for dep in dependencies
        ]
        graph[name] = list(dict.fromkeys(checked_dependencies))
    _validate_dependency_targets(graph)
    return graph


def _validate_dependency_targets(graph: dict[str, list[str]]) -> None:
    for package, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in graph:
                raise GraphError(
                    f"Пакет {package} зависит от отсутствующего "
                    f"пакета {dependency}."
                )


class _BfsTraversal:
    """Состояние рекурсивного обхода графа по уровням BFS."""

    def __init__(
        self,
        root_package: str,
        get_dependencies: Callable[[str], Iterable[str]],
        max_depth: int,
        package_filter: str | None,
    ) -> None:
        self.get_dependencies = get_dependencies
        self.max_depth = max_depth
        self.filter_value = (
            package_filter.casefold() if package_filter else None
        )
        self.graph: dict[str, list[str]] = {root_package: []}
        self.visited = {root_package}
        self.root_package = root_package

    def _filtered_dependencies(self, package: str) -> list[str]:
        dependencies = self.get_dependencies(package)
        if isinstance(dependencies, (str, bytes)):
            raise GraphError(
                f"Источник вернул некорректный список зависимостей "
                f"для пакета {package}."
            )
        unique_dependencies: list[str] = []
        for dependency in dependencies:
            if not isinstance(dependency, str) or not dependency:
                raise GraphError(
                    f"Источник вернул некорректное имя зависимости "
                    f"для пакета {package}."
                )
            if self.filter_value and self.filter_value in dependency.casefold():
                continue
            if dependency not in unique_dependencies:
                unique_dependencies.append(dependency)
        return unique_dependencies

    def _process_level(self, frontier: list[str], depth: int) -> None:
        next_frontier: list[str] = []
        for package in frontier:
            self.graph.setdefault(package, [])
            if depth >= self.max_depth:
                continue
            dependencies = self._filtered_dependencies(package)
            self.graph[package] = dependencies
            for dependency in dependencies:
                self.graph.setdefault(dependency, [])
                if dependency not in self.visited:
                    self.visited.add(dependency)
                    next_frontier.append(dependency)
        if next_frontier:
            self._process_level(next_frontier, depth + 1)

    def build(self) -> dict[str, list[str]]:
        try:
            self._process_level([self.root_package], 0)
        except RecursionError as exc:
            raise GraphError(
                "Граф слишком глубок для рекурсивного BFS. Уменьшите "
                "--max-depth или проверьте тестовый репозиторий."
            ) from exc
        return self.graph


def build_dependency_graph(
    root_package: str,
    get_dependencies: Callable[[str], Iterable[str]],
    max_depth: int,
    package_filter: str | None = None,
) -> dict[str, list[str]]:
    """Строит граф транзитивных зависимостей рекурсивным BFS.

    Обход выполняется по уровням: сначала обрабатываются все вершины
    текущей глубины, затем рекурсивно обрабатывается следующий уровень.
    """
    if not root_package:
        raise GraphError("Имя корневого пакета не должно быть пустым.")
    if max_depth < 0:
        raise GraphError("Максимальная глубина не может быть отрицательной.")
    traversal = _BfsTraversal(
        root_package,
        get_dependencies,
        max_depth,
        package_filter,
    )
    return traversal.build()
