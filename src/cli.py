from __future__ import annotations
import argparse
from typing import Sequence
from src.config import (
    AppConfig,
    ConfigError,
    non_negative_int,
    validate_config,
)
from npm_registry import (
    RegistryError,
    fetch_direct_dependencies,
)
def build_parser() -> argparse.ArgumentParser:
    description = (
        "Минимальный CLI-прототип визуализатора графа зависимостей. "
        "Этап 1 проверяет конфигурацию и выводит параметры."
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
            "HTTP(S)-URL или путь к локальному файлу тестового "
            "репозитория"
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
        help=(
            "максимальная глубина анализа; 0 означает только "
            "исходный пакет"
        ),
    )
    parser.add_argument(
        "--filter",
        dest="package_filter",
        metavar="SUBSTRING",
        help="необязательная подстрока для фильтрации пакетов",
    )
def print_config(config: AppConfig) -> None:
    package_filter = config.package_filter or "(не задан)"
    print("Параметры запуска:")
    print(f"package={config.package_name}")
    print(f"repository={config.repository}")
    print(f"test_repo_mode={config.test_repo_mode}")
    print(f"max_depth={config.max_depth}")
    print(f"package_filter={package_filter}")
    print(f"resolved_repository_mode={config.resolved_repo_mode}")
def _print_dependencies(
    dependencies: dict[str, str],
    package_filter: str | None,
) -> None:
    filtered = {
        name: version
        for name, version in dependencies.items()
        if not package_filter or package_filter.lower() in name.lower()
    }
    print()
    print(f"Прямые зависимости: {len(filtered)}")
    if not filtered:
        print("Зависимости не найдены.")
        return
    for name, version in filtered.items():
        print(f"{name} = {version}")
def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = validate_config(args)
        print_config(config)
        if config.resolved_repo_mode != "remote":
            raise ConfigError(
                "Для этапа 2 укажи URL реестра npm, "
                "например https://registry.npmjs.org"
            )
        version, dependencies = fetch_direct_dependencies(
            config.repository,
            config.package_name,
        )
        print(f"package_version={version}")
        _print_dependencies(dependencies, config.package_filter)
    except (ConfigError, RegistryError) as exc:
        print(f"Ошибка: {exc}", file=__import__("sys").stderr)
        return 2
    return 0