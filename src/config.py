from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
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
        message = "должно быть целым числом не меньше 0"
        raise argparse.ArgumentTypeError(message) from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("должно быть не меньше 0")
    return parsed
def is_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
    except ValueError:
        return False
    valid_scheme = parsed.scheme.lower() in {"http", "https"}
    return valid_scheme and bool(hostname)
def _validate_package(value: str | None) -> str:
    package_name = (value or "").strip()
    if not package_name:
        raise ConfigError(
            "параметр --package обязателен и не должен быть пустым."
        )
    return package_name
def _validate_repository_text(value: str | None) -> str:
    repository = (value or "").strip()
    if not repository:
        raise ConfigError(
            "параметр --repository обязателен и не должен быть пустым."
        )
    return repository
def _validate_mode(value: str | None) -> str:
    mode = (value or "auto").strip().lower()
    if mode not in MODES:
        allowed = ", ".join(MODES)
        raise ConfigError(
            "параметр --test-repo-mode должен принимать значения: "
            f"{allowed}."
        )
    return mode
def _validate_local_repository(repository: str) -> str:
    repo_path = Path(repository).expanduser()
    if not repo_path.exists():
        raise ConfigError(
            f"локальный файл репозитория не найден: {repository!r}."
        )
    if not repo_path.is_file():
        raise ConfigError(
            "путь репозитория должен указывать на файл, а не на "
            f"каталог: {repository!r}."
        )
    try:
        with repo_path.open("rb"):
            pass
    except OSError as exc:
        raise ConfigError(
            "локальный файл репозитория недоступен для чтения: "
            f"{repository!r}."
        ) from exc
    return str(repo_path.resolve())
def _resolve_repository(repository: str, mode: str) -> tuple[str, str]:
    is_url = is_http_url(repository)
    looks_like_url = "://" in repository
    if looks_like_url and not is_url:
        raise ConfigError(
            "параметр --repository содержит некорректный URL; "
            "поддерживаются http:// или https:// с именем хоста."
        )
    if mode == "remote":
        if not is_url:
            raise ConfigError(
                "для режима remote параметр --repository должен быть "
                "корректным HTTP(S)-URL."
            )
        return repository, "remote"
    if mode == "local" and is_url:
        raise ConfigError(
            "для режима local параметр --repository должен указывать "
            "на локальный файл, а не URL."
        )
    if is_url:
        return repository, "remote"
    return _validate_local_repository(repository), "local"
def _validate_filter(value: str | None) -> str | None:
    if value is None:
        return None
    package_filter = value.strip()
    if not package_filter:
        raise ConfigError(
            "параметр --filter не должен быть пустым; чтобы отключить "
            "фильтр, не указывайте его."
        )
    return package_filter
def _validate_depth(value: int | None) -> int:
    if value is None or value < 0:
        raise ConfigError(
            "параметр --max-depth должен быть целым числом не меньше 0."
        )
    return value
def validate_config(args: argparse.Namespace) -> AppConfig:
    package_name = _validate_package(args.package)
    repository = _validate_repository_text(args.repository)
    mode = _validate_mode(args.test_repo_mode)
    normalized_repo, resolved_mode = _resolve_repository(repository, mode)
    package_filter = _validate_filter(args.package_filter)
    max_depth = _validate_depth(args.max_depth)
    return AppConfig(
        package_name=package_name,
        repository=normalized_repo,
        test_repo_mode=mode,
        resolved_repo_mode=resolved_mode,
        max_depth=max_depth,
        package_filter=package_filter,
    )