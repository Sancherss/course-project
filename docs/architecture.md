# Надстройка и границы ответственности

- `config.py`: immutable dataclass, whitelist реальных scenario/CTAP/property/fields/entity индексов, pin commit, валидация IDs и времени. `precise_actions` — собственная настройка запуска ProVerif, не upstream threat flag.
- `upstream.py`: worker в отдельном процессе/TemporaryDirectory. Загружает оригинальный Python с запретом bytecode, создаёт Generator/Case, вызывает write_file(False), копирует input и библиотеку. Не вызывает ошибочные upstream analyze/proverif.
- `runner.py`: уникальные каталоги raw/generated, stdout/stderr файловыми дескрипторами, process group timeout, exit code, metadata с input/executable/manager-source SHA256 и командами.
- `parser.py` / `results.py`: консервативная классификация документированных RESULT, отдельный ERROR/UNKNOWN; supplementary записи подтверждены source ProVerif. Класс не заменяет смысла конкретного query.
- `matrix.py`: последовательное выполнение одной конфигурационной серии; `--only ID` выбирает один существующий случай.
- `report.py`: повторно разбирает immutable raw текущим parser; создаёт новый timestamp snapshot CSV/JSON/Markdown и parser-provenance, не переписывая старые.
- `cli.py`: команды `run` и `summary`; `python -m experiment_manager` и установленный `fido2-experiments` эквивалентны.
- `scripts/check_environment.py`: read-only проверка Python, verifier version, pin и чистоты upstream.
- `scripts/run_baseline.py`: отдельный stdlib-runner прямой upstream модели P1, без импорта исторического скрипта.

Данные идут по цепочке YAML → validated configuration → isolated original generator → generated model + identical library → ProVerif → full raw → parsed snapshot. Полные модели дублируются в raw, чтобы результат не зависел от последующего удаления generated.

При ERROR/UNKNOWN первичные данные сохраняются. Ненулевой exit code и Error diagnostics не классифицируются как атака. Timeout означает неполный анализ. В диагностике `not event` false означает достижимость. В эквивалентностях не обещается одинаковая семантика контрпримеров с обычной secrecy проверкой.

После первого пилота обнаруженный __pycache__ был удалён; source-файлы не изменялись. Worker теперь запрещает запись bytecode двумя способами — переменной окружения и sys.dont_write_bytecode. Это проверяется тестом фактической чистоты checkout.

Follow-up: параметр single_session_witness разрешён только для diagnostic D-finish. Exact replacement одного корневого !system проверяется как отдельная операция. Processed interpretation различает ложность security query и положительную диагностику достижимости; поля status и первичный RESULT остаются неизменными.
