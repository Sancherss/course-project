# Воспроизведение baseline P1

**VERIFIED EXPERIMENTALLY** · 14.11.2026.

- Run ID: `20261114T173042063564Z-baseline-05290b45`.
- Команда: `.tools/proverif/proverif -lib FIDO2.pvl Reg_unlink.pv`; исполняемый файл использован по абсолютному пути, cwd — уникальная raw-директория с неизменёнными копиями двух входных файлов.
- Модель: getToken/client, регистрация, CA/CR private, без дополнительных утечек и ролей; choice[wk,wk1] из исходного Reg_unlink.pv.
- FIDO2Verif commit: `2d8eaf326117bd7e4706c48b2d24e27b4a006fa6`. Недоступный тег version_1.0 не используется как подтверждённая версия.
- ProVerif: 2.05, собран из официального source tarball с OCaml 4.14.2. Python 3.12.14; Linux x86_64, glibc 2.41.
- Exit code: 0. Timeout: нет. Duration: 0.16435877599997184 s; это время анализатора, не протокола.
- Точный ответ: `RESULT Observational equivalence is true.`
- stderr пуст; stdout содержит termination warnings, которые сохранены. Наличие предупреждений не скрылось за успешной классификацией.

Raw: `experiments/raw/20261114T173042063564Z-baseline-05290b45/` содержит metadata.json, stdout.txt, stderr.txt, command.txt, FIDO2.pvl и Reg_unlink.pv. Метаданные включают SHA256 обоих inputs и executable.

Результат согласуется с §5.1 / Privacy Properties статьи Guan et al., где P1 заявлено выполненным для регистрации. Это ограниченное воспроизведение одного случая, а не всех таблиц статьи. Оно не доказывает секретность PinToken и не переносится автоматически на CTAP 2.3.
