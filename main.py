from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from typing import Sequence
MODES = ("auto", "local", "remote")
@dataclass(frozen=True)
class AppConfig:
    package_name: str
    repository: str
    test_repo_mode: str
    resolved_repo_mode: str
    max_depth: int
    package_filter: str | None
class ConfigError(ValueError):
    pass
def non_negative_int(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "должно быть целым числом не меньше 0"
        ) from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("должно быть не меньше 0")
    return parsed
def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
def validate_config(args: argparse.Namespace) -> AppConfig:
    package_name = (args.package or "").strip()
    if not package_name:
        raise ConfigError("параметр --package обязателен и не должен быть пустым.")
    raw_repository = (args.repository or "").strip()
    if not raw_repository:
        raise ConfigError("параметр --repository обязателен и не должен быть пустым.")
    mode = (args.test_repo_mode or "auto").strip().lower()
    if mode not in MODES:
        allowed = ", ".join(MODES)
        raise ConfigError(
            f"параметр --test-repo-mode должен принимать одно из значений: {allowed}."
        )
    is_url = is_http_url(raw_repository)
    looks_like_url = "://" in raw_repository
    if looks_like_url and not is_url:
        raise ConfigError(
            "параметр --repository содержит некорректный URL; "
            "поддерживаются URL с протоколом http:// или https:// и именем хоста."
        )
    if mode == "remote":
        if not is_url:
            raise ConfigError(
                "для режима remote параметр --repository должен быть корректным HTTP(S)-URL."
            )
        normalized_repository = raw_repository
        resolved_mode = "remote"
    else:
        if mode == "local" and is_url:
            raise ConfigError(
                "для режима local параметр --repository должен указывать на локальный файл, а не URL."
            )
        if is_url and mode == "auto":
            normalized_repository = raw_repository
            resolved_mode = "remote"
        else:
            repo_path = Path(raw_repository).expanduser()
            if not repo_path.exists():
                raise ConfigError(
                    f"локальный файл репозитория не найден: {raw_repository!r}."
                )
            if not repo_path.is_file():
                raise ConfigError(
                    f"путь репозитория должен указывать на файл, а не на каталог: {raw_repository!r}."
                )
            try:
                with repo_path.open("rb"):
                    pass
            except OSError as exc:
                raise ConfigError(
                    f"локальный файл репозитория недоступен для чтения: {raw_repository!r}."
                ) from exc
            normalized_repository = str(repo_path.resolve())
            resolved_mode = "local"
    package_filter = args.package_filter
    if package_filter is not None:
        package_filter = package_filter.strip()
        if not package_filter:
            raise ConfigError(
                "параметр --filter не должен быть пустым; чтобы отключить фильтр, не указывайте его."
            )
    max_depth = args.max_depth
    if max_depth is None or max_depth < 0:
        raise ConfigError("параметр --max-depth должен быть целым числом не меньше 0.")
    return AppConfig(
        package_name=package_name,
        repository=normalized_repository,
        test_repo_mode=mode,
        resolved_repo_mode=resolved_mode,
        max_depth=max_depth,
        package_filter=package_filter,
    )
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Минимальный CLI-прототип визуализатора графа зависимостей пакетов. "
            "На этапе 1 приложение проверяет конфигурацию и выводит параметры."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--package",
        metavar="NAME",
        help="имя анализируемого пакета (обязательный параметр)",
    )
    parser.add_argument(
        "--repository",
        metavar="URL_OR_PATH",
        help="HTTP(S)-URL репозитория или путь к локальному файлу тестового репозитория",
    )
    parser.add_argument(
        "--test-repo-mode",
        default="auto",
        metavar="MODE",
        help="режим репозитория: auto, local или remote",
    )
    parser.add_argument(
        "--max-depth",
        type=non_negative_int,
        default=3,
        metavar="N",
        help="максимальная глубина анализа зависимостей (0 означает только исходный пакет)",
    )
    parser.add_argument(
        "--filter",
        dest="package_filter",
        metavar="SUBSTRING",
        help="необязательная подстрока для фильтрации пакетов",
    )
    return parser
def print_config(config: AppConfig) -> None:
    print("Параметры запуска:")
    print(f"package={config.package_name}")
    print(f"repository={config.repository}")
    print(f"test_repo_mode={config.test_repo_mode}")
    print(f"max_depth={config.max_depth}")
    print(f"package_filter={config.package_filter if config.package_filter is not None else '(не задан)'}")
    print(f"resolved_repository_mode={config.resolved_repo_mode}")
    print()
    print("Конфигурация проверена успешно. Анализ зависимостей будет добавлен на следующих этапах.")
def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = validate_config(args)
    except ConfigError as exc:
        parser.error(str(exc))
    print_config(config)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())