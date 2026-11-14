# Сценарий демонстрации

1. Открыть README и объяснить, что исследуется модель ESORICS 2022, а не реальный сервис. Показать docs/specification_gap.md и подтверждённый CTAP 2.3.
2. Запустить `make check`: версии, commit и чистота upstream.
3. Показать docs/baseline_reproduction.md и raw-команду P1. При необходимости `make baseline` создаёт **новый** независимый журнал.
4. Показать experiments/configs/matrix.yaml: E0/E1/E2, две фазы и два свойства. Разобрать дополнительные роли по исходному RegEntities, не называть их полным захватом устройства.
5. Для быстрой демонстрации выполнить `.venv/bin/python -m experiment_manager run experiments/configs/matrix.yaml --only R05`. Это дополнительный запуск сверх исходных 24, с новым run ID; он не нужен для просмотра готовых результатов.
6. Выполнить `make summary` и открыть новый summary.md. Различить PROVED, UNKNOWN/cannot be proved, UNKNOWN/timeout, ATTACK_OR_FALSE.
7. Сопоставить R01/R02/R03: секретность доказана/не установлена/доказана. Показать, что trace с hypothesis не переименован в подтверждённую утечку.
8. Открыть raw R05: false A6 и `A trace has been found.`. Показать дополнительные роли и границы доверия в модели.
9. Показать precision.yaml: это официальная настройка решателя, а не изменение threat assumptions. Сравнить A1 E0 при default timeout и preciseActions.
10. Запустить `make test`, показать tests с реальными outputs и проверками изоляции. Затем открыть report/coursework_draft.md или DOCX и обозначить незаполненные персональные/локальные требования.

Не тестировать реальные сайты, устройства или чужую инфраструктуру. Все демонстрационные команды работают только с локальными формальными моделями.
