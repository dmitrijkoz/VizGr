# Визуализатор графа зависимостей пакетов — этап 1

Минимальный CLI-прототип на Python 3.10+ без сторонних библиотек. На первом этапе приложение принимает и проверяет конфигурацию, а затем выводит параметры в формате `ключ=значение`. Получение и визуализация зависимостей относятся к следующим этапам.

## Параметры командной строки

| Параметр | Обязательный | Назначение | Проверка |
|---|---:|---|---|
| `--package NAME` | Да | Имя анализируемого пакета | Не может быть пустым или состоять только из пробелов |
| `--repository URL_OR_PATH` | Да | HTTP(S)-URL либо путь к локальному файлу тестового репозитория | URL должен иметь `http`/`https` и имя хоста; локальный путь должен указывать на существующий файл |
| `--test-repo-mode MODE` | Нет | Режим работы с тестовым репозиторием: `auto`, `local`, `remote` | Проверяется допустимое значение и его согласованность с репозиторием |
| `--max-depth N` | Нет | Максимальная глубина анализа | Целое число `>= 0`; значение `0` означает анализ только исходного пакета |
| `--filter SUBSTRING` | Нет | Подстрока для фильтрации пакетов | Если параметр указан, подстрока не должна быть пустой |

Значения по умолчанию: `--test-repo-mode auto`, `--max-depth 3`; фильтр по умолчанию не задан.

В режиме `auto` приложение самостоятельно определяет тип источника: HTTP(S)-URL — удалённый репозиторий, существующий файл — локальный. В режиме `local` принимается путь к файлу, в режиме `remote` — HTTP(S)-URL. На этапе 1 удалённый ресурс не скачивается и не анализируется.

## Запуск

Требуется Python 3.10 или новее. Дополнительные зависимости устанавливать не нужно.

### Windows

```bat
run.bat --package demo-app --repository test-repository.json --test-repo-mode local --max-depth 2 --filter demo
```

### Linux / macOS

```sh
./run.sh --package demo-app --repository test-repository.json --test-repo-mode local --max-depth 2 --filter demo
```

### Посмотреть справку

```sh
python main.py --help
```

### Пример вывода

```text
Параметры запуска:
package=demo-app
repository=/полный/путь/к/test-repository.json
test_repo_mode=local
max_depth=2
package_filter=demo
resolved_repository_mode=local

Конфигурация проверена успешно. Анализ зависимостей будет добавлен на следующих этапах.
```

## Демонстрация обработки ошибок

Команды следует запускать из каталога проекта.

```sh
# Нет обязательного имени пакета
python main.py --repository test-repository.json

# Нет обязательного репозитория
python main.py --package demo-app

# Файл не существует
python main.py --package demo-app --repository missing.json

# Недопустимый режим
python main.py --package demo-app --repository test-repository.json --test-repo-mode production

# Глубина не может быть отрицательной или нецелой
python main.py --package demo-app --repository test-repository.json --max-depth -1
python main.py --package demo-app --repository test-repository.json --max-depth abc

# Пустая подстрока фильтра недопустима
python main.py --package demo-app --repository test-repository.json --filter ""

# Тип источника не соответствует указанному режиму
python main.py --package demo-app --repository test-repository.json --test-repo-mode remote
```

При ошибке приложение выводит сообщение в `stderr` и завершает работу с кодом `2`.

## Тестирование

```sh
python -m unittest discover -s tests -v
```

## Структура проекта

- `main.py` — аргументы CLI, валидация конфигурации и вывод `ключ=значение`.
- `test-repository.json` — небольшой учебный файл репозитория для успешного запуска.
- `tests/test_config.py` — модульные тесты корректной конфигурации и ошибок параметров.
- `run.bat`, `run.sh` — скрипты запуска.
