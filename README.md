# Курсовой проект: экспериментальный анализ FIDO2Verif

**GENERATED DRAFT** для самостоятельной проверки студентом и руководителем БГУ. Основная тема: «Разработка программных средств для экспериментального анализа безопасности протокола FIDO2 на основе FIDO2Verif».

## Полученный результат

- Зафиксирован неизменённый upstream commit `2d8eaf326117bd7e4706c48b2d24e27b4a006fa6` в Git submodule.
- Локально собраны OCaml 4.14.2 и ProVerif 2.05; окружение проверено.
- P1 baseline регистрации вернул **Observational equivalence is true**, что согласуется с §5.1 статьи ESORICS 2022.
- Реализован experiment_manager: изолированная генерация через исходный Python API, полный raw/provenance, консервативный parser, CSV/JSON/Markdown snapshots.
- Выполнены **27 модельных запусков**: первоначальные 24 и три дополнительные диагностики достижимости. Первоначальная серия: 12 основных + baseline/пилот/диагностика/проверки точности. В основной матрице 6 PROVED, 1 false A6 с trace, 5 UNKNOWN. UNKNOWN не считается атакой.
- **35 тестов прошли**; проверены хеши всех inputs, идентичность библиотеки и чистота upstream.
- Подготовлены первоисточники, анализ требований БГУ, сравнение модели 2022 с WebAuthn Level 3 / CTAP 2.3, черновик записки Markdown/DOCX и сценарий демонстрации.

Это законченный ограниченный исследовательский MVP и черновик записки, **не окончательно оформленная работа для сдачи**. Реквизиты, локальные требования, библиография и научные формулировки требуют проверки. Невакуозность доказанных A6 E0/E2 и A1 E0 подтверждена дополнительными положительными single-session traces; см. docs/nonvacuity_witnesses.md. Прежние UNKNOWN не переписываются.

## Быстрый просмотр

- `docs/results_analysis.md` — результаты и ограничения.
- `experiments/processed/20261114T175612262785Z/summary.md` — итоговая таблица; рядом CSV/JSON, matrix_results.yaml и parser-provenance.json.
- `report/coursework_draft.md`, `report/coursework_draft.docx` — редактируемый черновик записки.
- `report/figures/matrix.png`, `report/figures/matrix.svg` — проверенная визуальная сводка основной матрицы.
- `docs/baseline_reproduction.md` — один непосредственно сверенный со статьёй baseline.
- `docs/repository_analysis.md`, `docs/paper_analysis.md`, `docs/specification_gap.md` — код, статья и современные спецификации.
- `docs/bsu_formatting_requirements.md`, `report/format_checklist.md` — только подтверждённые нормы БГУ и открытые вопросы.
- `docs/environment.md`, `docs/architecture.md`, `docs/demo.md` — воспроизведение, устройство надстройки и демонстрация.

## Установка

Нужны Linux/WSL, Python 3.10+, Git; для локальной сборки инструмента — curl, sha256sum, tar, gcc и make. На данном окружении проверены Python 3.12.14 и Linux x86_64. Нативный Windows-вариант надстройки не проверен.

Из корня проекта:

```sh
git submodule update --init
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
./scripts/bootstrap_proverif.sh
.venv/bin/python scripts/check_environment.py
```

При распаковке полного архива upstream уже вложен вместе с локальной историей. Bootstrap скачивает официальные архивы и проверяет SHA256; не использует поставляемый upstream Windows exe. Если нативный ProVerif установлен отдельно, задайте `PROVERIF=/absolute/path/to/proverif`. Выполняемые опции проверены по README и официальным исходникам ProVerif. Никаких реальных сайтов и устройств команды не тестируют.

## Воспроизведение

```sh
# Один документированный upstream baseline; новый уникальный raw-каталог
.venv/bin/python scripts/run_baseline.py

# 12 основных измерений; каждый повтор создаёт новые raw и generated
.venv/bin/python -m experiment_manager run experiments/configs/matrix.yaml

# При необходимости: 6 диагностик и 4 solver sensitivity измерения
.venv/bin/python -m experiment_manager run experiments/configs/diagnostics.yaml
.venv/bin/python -m experiment_manager run experiments/configs/precision.yaml

# Три положительных свидетеля достижимости (follow-up, отдельная серия)
.venv/bin/python -m experiment_manager run experiments/configs/witnesses.yaml

# Новый неизменяемый summary snapshot всех сохранённых raw-журналов
.venv/bin/python -m experiment_manager summary

# Тесты собственного Python; ProVerif заново не запускают
.venv/bin/python -m pytest -q

# Аудит исходного сохранённого набора evidence
.venv/bin/python scripts/verify_artifacts.py

# Экспорт редактируемого черновика
.venv/bin/python scripts/export_report.py
```

Эквивалентные цели: `make check baseline matrix diagnostics precision witnesses summary test report verify`. `make install` создаёт venv и ставит Python dependencies, `make tools` собирает verifier. После editable install доступна команда `fido2-experiments`.

Один случай: `.venv/bin/python -m experiment_manager run experiments/configs/matrix.yaml --only R05`. Это **дополнительный** запуск, он не подменяет сохранённый исходный R05.

`verify_artifacts.py` сопоставляет все raw с зафиксированным финальным snapshot. После собственных новых прогонов создайте summary и обновите evidence/final-summary-location.txt на новый snapshot; исходные 24 запуска, три дополнительных witness-запуска и исторические snapshots сохраняются.

## Формат результата и чтение статусов

Каждый `experiments/raw/<unique-run-id>/` содержит metadata.json, command.txt, stdout.txt, stderr.txt, model.pv/FIDO2.pvl (для baseline Reg_unlink.pv), конфигурацию и журналы генератора. metadata включает версию и SHA256 executable, commit upstream, SHA256 inputs, время UTC, duration, exit code и timeout. `generated/` хранит соответствующую копию input.

- PROVED — распознанный окончательный RESULT true при успешном завершении.
- ATTACK_OR_FALSE — RESULT false; смысл зависит от query. Для диагностического `not event` это достижимость, **не атака**.
- UNKNOWN — cannot be proved, timeout или неизвестный формат; причина сохраняется.
- ERROR — ошибка генерации/процесса или явная диагностика ошибки.

Processed summary повторно разбирает raw актуальным parser. Это существенно для R05: первая версия parser сохранила в metadata UNKNOWN из-за supplementary RESULT; текущий parser подтверждён исходником ProVerif и правильно относит основной запрос к false. Старые raw metadata не переписываются. SHA256 parser входит в каждый summary snapshot.

## Границы исследования

Исторический S-pintok охватывает несколько bindings; отдельный fresh token не выделялся новым query. E1/E2 — предусмотренные upstream дополнительные сеансы с публичным интерфейсом, а не полный дамп памяти или глобальная публикация CA/CR. Default A1 в основной матрице не завершился за 60 s; preciseActions=true доказал A1 только для E0. Несмотря на UNKNOWN исходных reachability диагностик, три исполнимых single-session traces подтверждают достижимость завершающих событий для всех трёх доказанных конфигураций A6 E0/E2 и A1 E0. Положительные traces вкладываются в исходную репликацию; bounded security proofs не применяются.

README upstream упоминает version_1.0, но сервер не возвращает тегов; не заявляется полная идентичность доступного HEAD paper artifact. Внешние спецификации используются только для gap analysis. Современные pinUvAuthToken/permissions/lifecycle, backup и другие механизмы не добавлялись в модель.

## Авторы и исходные материалы

Исходная модель и опубликованные результаты: Jingjing Guan, Hui Li, Haisong Ye, Ziming Zhao, «A Formal Analysis of the FIDO2 Protocols», ESORICS 2022, DOI 10.1007/978-3-031-17143-7_1, CactiLab/FIDO2Verif. Собственная часть проекта — надстройка, ограниченные измерения и документированный сравнительный анализ. Источники и дата обращения: docs/sources.md.

Документы БГУ подтверждают структуру, форму задания/титула и нумерацию; численные параметры оформления КП по неизвестной кафедре не выдумываются. DOCX сохраняет стандартное оформление Word без утверждения о его соответствии локальной методичке.
