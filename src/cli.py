from __future__ import annotations

import argparse
import sys
from typing import Sequence

from src.config import (
    AppConfig,
    ConfigError,
    non_negative_int,
    validate_config,
)
from src.dependency_graph import (
    GraphError,
    build_dependency_graph,
    load_test_repository,
)
from npm_registry import RegistryError, fetch_direct_dependencies


def build_parser() -> argparse.ArgumentParser:
    """Создаёт парсер параметров командной строки."""
    description = (
        "Визуализатор графа зависимостей npm. "
        "Этап 3 строит транзитивный граф алгоритмом BFS."
    )
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    _add_required_arguments(parser)
    _add_optional_arguments(parser)
    return parser


def _add_required_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--package",
        metavar="NAME",
        help="имя анализируемого пакета (обязательный параметр)",
    )
    parser.add_argument(
        "--repository",
        metavar="URL_OR_PATH",
        help=(
            "HTTP(S)-URL npm Registry или путь к JSON-файлу "
            "тестового репозитория"
        ),
    )


def _add_optional_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--test-repo-mode",
        default="auto",
        metavar="MODE",
        help="режим работы с репозиторием: auto, local или remote",
    )
    parser.add_argument(
        "--max-depth",
        type=non_negative_int,
        default=3,
        metavar="N",
        help="максимальная глубина; 0 означает только корневой пакет",
    )
    parser.add_argument(
        "--filter",
        dest="package_filter",
        metavar="SUBSTRING",
        help="исключить пакеты, в имени которых есть эта подстрока",
    )


def print_config(config: AppConfig) -> None:
    """Печатает нормализованные параметры запуска."""
    package_filter = config.package_filter or "(не задан)"
    print("Параметры запуска:")
    print(f"package={config.package_name}")
    print(f"repository={config.repository}")
    print(f"test_repo_mode={config.test_repo_mode}")
    print(f"max_depth={config.max_depth}")
    print(f"package_filter={package_filter}")
    print(f"resolved_repository_mode={config.resolved_repo_mode}")


def _print_graph(graph: dict[str, list[str]]) -> None:
    print("\nГраф зависимостей (BFS):")
    edge_count = 0
    for package, dependencies in graph.items():
        edge_count += len(dependencies)
        rendered = ", ".join(dependencies) if dependencies else "нет"
        print(f"  {package} -> {rendered}")
    print(f"\nПакетов в графе: {len(graph)}")
    print(f"Связей в графе: {edge_count}")


def _build_remote_graph(
    config: AppConfig,
) -> tuple[dict[str, list[str]], dict[str, str]]:
    versions: dict[str, str] = {}

    def get_dependencies(package: str) -> list[str]:
        version, dependencies = fetch_direct_dependencies(
            config.repository,
            package,
        )
        versions[package] = version
        return list(dependencies)

    graph = build_dependency_graph(
        config.package_name,
        get_dependencies,
        config.max_depth,
        config.package_filter,
    )
    return graph, versions


def _build_local_graph(
    config: AppConfig,
) -> dict[str, list[str]]:
    repository_graph = _load_repository(config)
    if config.package_name not in repository_graph:
        raise GraphError(
            f"Пакет {config.package_name} отсутствует в тестовом "
            "репозитории."
        )

    def get_dependencies(package: str) -> list[str]:
        return repository_graph[package]

    return build_dependency_graph(
        config.package_name,
        get_dependencies,
        config.max_depth,
        config.package_filter,
    )


def _load_repository(config: AppConfig) -> dict[str, list[str]]:
    return load_test_repository(config.repository)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = validate_config(args)
        print_config(config)
        versions: dict[str, str] = {}
        if config.resolved_repo_mode == "local":
            graph = _build_local_graph(config)
        else:
            graph, versions = _build_remote_graph(config)
        if versions:
            root_version = versions.get(config.package_name)
            if root_version:
                print(f"package_version={root_version}")
            print("\nВерсии обработанных пакетов:")
            for package, version in versions.items():
                print(f"  {package} = {version}")
        _print_graph(graph)
    except (ConfigError, GraphError, RegistryError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2
    return 0
