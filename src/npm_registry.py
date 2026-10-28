from __future__ import annotations
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
class RegistryError(ValueError):
    pass
def _build_metadata_url(repository: str, package: str) -> str:
    base = repository.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RegistryError("Указан некорректный URL реестра npm.")
    encoded_package = quote(package, safe="@")
    return f"{base}/{encoded_package}"
def _read_json(url: str) -> dict:
    request = Request(
        url,
        headers={"Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            data = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            raise RegistryError(
                "Пакет не найден в указанном реестре npm."
            ) from exc
        raise RegistryError(
            f"Реестр npm вернул HTTP {exc.code}."
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RegistryError(
            f"Не удалось получить данные из реестра npm: {exc}"
        ) from exc
    try:
        result = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegistryError(
            "Реестр вернул некорректные JSON-данные."
        ) from exc
    if not isinstance(result, dict):
        raise RegistryError("Формат метаданных npm некорректен.")
    return result
def fetch_direct_dependencies(
    repository: str,
    package: str,
) -> tuple[str, dict[str, str]]:
    url = _build_metadata_url(repository, package)
    metadata = _read_json(url)
    dist_tags = metadata.get("dist-tags", {})
    version = dist_tags.get("latest") if isinstance(
        dist_tags, dict
    ) else None
    if not isinstance(version, str) or not version:
        raise RegistryError(
            "В метаданных npm отсутствует версия latest."
        )
    versions = metadata.get("versions", {})
    version_data = versions.get(version, {}) if isinstance(
        versions, dict
    ) else {}
    if not isinstance(version_data, dict):
        raise RegistryError("Данные версии пакета некорректны.")
    dependencies = version_data.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise RegistryError("Поле dependencies имеет неверный формат.")
    normalized: dict[str, str] = {}
    for name, requirement in dependencies.items():
        if isinstance(name, str) and isinstance(requirement, str):
            normalized[name] = requirement
    return version, dict(sorted(normalized.items()))