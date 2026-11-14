# Исследование FIDO2Verif

VERIFIED FROM SOURCE · 14.11.2026. Исследовательский этап, без реализации надстройки.
Все пути FILE ниже относительно `upstream/FIDO2Verif/`. Ссылки на строки относятся исключительно к зафиксированному commit.

## 1. Происхождение и окружение

- Remote: https://github.com/CactiLab/FIDO2Verif.
- HEAD: `2d8eaf326117bd7e4706c48b2d24e27b4a006fa6`, commit «readme», 12.05.2022 (дата автора).
- `git tag` и `git ls-remote --tags origin` вернули пустые списки. Тег `version_1.0` упомянут в README, но при проверке не опубликован сервером. Этот commit нельзя обозначать как проверенный paper tag.
- README: Python 3.0+, ProVerif 2.01+, `proverif.exe` рядом со скриптом; путь без пробелов. FILE: README.md; REGION: Software Requirements.
- Фактическое окружение исследования: Linux, Python 3.12.14; ProVerif отсутствует в PATH, OCaml-компилятор не найден. Поставляемый `proverif.exe` — Windows PE32+ x86-64, не нативный Linux executable. Формальная проверка не запускалась.
- Машиночитаемые сведения: `evidence/provenance.json`.

## 2. Полная структура значимых файлов

| FILE | Назначение и REGION |
|---|---|
| README.md | Связь с ESORICS 2022, требования и команды; Software Requirements / File Organization / Verify… |
| FIDO2Verif.py | Единственная Python-точка входа; `if __name__ == '__main__'`, строки 869–933; генерация, запуск, классификация |
| FIDO2.pvl | Типы, криптографические операции, каналы, таблицы, события и роли; строки 1–875; `CTAP_Authnr`, `CTAP_Client`, `Reg_*`, `Auth_*`, `get_creid` |
| Reg.pv | Шаблон регистрации; `system`, `process`, 1–58. Сам по себе не готов: ctap_type/au_type закомментированы, query добавляет Python |
| Auth.pv | Шаблон аутентификации и транзакций; `system`, `process`; таблицы регистрации предварительно заполняются, строки 13–17 |
| Reg_unlink.pv | Готовый biprocess регистрации: `choice[wk,wk1]`, строка 48; параметры 8–10 |
| Auth_unlink.pv | Biprocess аутентификации: `choice[wk,wk1]`, строка 58; параметры 8–13 |
| Auth_A3_A4.pv | Специальные три группы сеансов для leak resilience; query 1–2; process 4–121; несовместимые с текущей библиотекой вызовы, см. ниже |
| proverif.exe | Поставляемый Windows binary; версия в ходе исследования не установлена |
| FIDO2Verif.zip | Вложенная копия проекта. Не использовать вместо корневых файлов: в архивной FIDO2.pvl иначе закрыт комментарий перед Constant Declaration |

README ошибочно называет Python-скрипт `FIDO2Verif.pv`; реальное имя `FIDO2Verif.py`. Отдельных конфигурационных файлов, готовых LOG/TEMP/Result и тестов в рабочем дереве нет. REGION: `git ls-files`, README / File Organization.

## 3. Реальные CLI-параметры

FILE: FIDO2Verif.py; REGION: print_help (853–867), getopt и dispatch (888–921).

| Рекомендуемая форма | Действие |
|---|---|
| `-h`, `--help` | Справка; **не read-only**, см. побочные эффекты |
| `-t NAME`, `--target NAME` | Одна группа сценариев, не один эксперимент |
| `-s` | Без дополнительных утечек полей; все комбинации дополнительных ролей остаются |
| Без аргументов | Восемь потоков анализа восьми групп |

NAME: `reg_client`, `reg_server`, `auth_client_em`, `auth_client_sim`, `auth_client_gen`, `auth_server_em`, `auth_server_sim`, `auth_server_gen`. FILE: классы Types (153–198), main (879–921).

В README указаны однотирейные `-help`, `-target`, `-simple`, но строка коротких опций getopt некорректна. Без импорта upstream проверено стандартным `getopt` Python 3.12.14:

- `-target reg_client` разбирается как `('-t', 'arget')` с остатком `reg_client`; корректного выбора цели не будет.
- `-simple` разбирается как набор коротких опций `-s -i -m -p -l -e`; появляются сообщения wrong option.
- `-help` разбирается как `-h -e -l -p`, хотя первый `-h` завершает программу справкой.
- `--simple` отклоняется. Ветви обработки `--t` и иных имён не означают отдельные документированные параметры (getopt допускает сокращение --target).

Нет CLI для одного query, CTAPType, набора утечек, набора ролей, timeout, executable или output directory. Не предлагать вымышленные `--compromised-client`, `--query`, `--pin-token`.

## 4. Параметры модели и генерация

FILE: FIDO2Verif.py; REGION: AllCTAPType (144–150), Types (153–198), AllFields/RegFields/AuthFields (405–459), RegEntities/AuthEntities (358–391), Generator (574–785).

- CTAP: `noCTAP`, `setPIN`, `chgPIN`, `getToken`.
- Хранение: `client`, `server`. Это места хранения credential private key в исторической модели, а не современные platform/cross-platform или backup-eligible категории.
- Транзакции: `empty`, `simple`, `generic` (только аутентификация).
- Утечки регистрации: `out(cP,wk);`, `out(cP,skat);`, их подмножества.
- Утечки аутентификации: `wk`, `skau`, `authcntr`, `creid`, их подмножества.
- Дополнительные роли: пять вариантов, все 32 подмножества. Пример регистрации: index 1 `Reg_Client(uHandle,pWord,CR,cP,ctap_type)`; index 2 `Reg_Client(uHandle,pWord,cP,CA,ctap_type)`. При CTAP дополнительно для index 0 вставляется CTAP_Authnr на cP, для index 1 — CTAP_Client на cP (Case.write_file, 509–516).
- Важно: исходные честные роли сохраняются. Это добавление сеансов с публичными интерфейсами, а не глобальная замена CA/CR на публичные каналы или полный дамп памяти устройства.
- Классы `RegEntitiesV2`, `AuthEntitiesV2` существуют, но Generator использует обычные RegEntities/AuthEntities. Комментарии V2 нельзя выдавать за фактическую конфигурацию запуска.

`Case.write_file` (482–519) добавляет query в начало, вставляет настройки по **фиксированным нулевым индексам строк** Setting (31–40), утечки и роли. `analyze` (521–542) сначала удаляет все `!` и проверяет ограниченный вариант; если ответ не false, повторяет с исходной репликацией. `Generator.reverse_f_e`, `jump_if_its_secure` меняют порядок и пропускают подмножества, а не выполняют каждый случай независимо.

Без редактирования PV-кода CLI позволяет выбрать группу и отключить утечки. Для точечной матрицы можно впоследствии вызывать существующие объекты Type/CTAPType/Query/Fields/Entities/Case из изолированной копии; это Python API, **не готовая CLI-возможность**. Не импортировать upstream в оригинальном каталоге.

## 5. Реальные security queries

FILE: FIDO2Verif.py; REGION: AllQueries и subclasses, 201–311.

| Имя | Точный запрос/смысл | Где применяется |
|---|---|---|
| S-pintok | `query secret PinToken.` | Все группы |
| S-cntr | `query secret testcntr.` | Все группы |
| S-creid | `query secret testcreid.` | Все группы |
| S-skau | `query secret skau.` | Все группы |
| S-skat | `query secret skat.` | Регистрация |
| S-wk | `query secret wk.` | Регистрация server, аутентификация server |
| S-tr | `query secret Tr.` (AuthClientTrQueries); **`query secret tr.`** (AuthServerTrQueries) | Транзакции; различие регистра требует проверки |
| A5 | `inj-event(Server_Finish_Reg(u,r,a,c,pkau)) ==> inj-event(Client_Init_Reg(u,r))` | Регистрация |
| A6 | `inj-event(Server_Finish_Reg(u,r,a,c,pkau)) ==> inj-event(Authnr_Finish_Reg(u,r,a,c,pkau))` | Регистрация |
| A1 | `inj-event(Server_Finish_Auth(u,r,a,c)) ==> inj-event(Authnr_Finish_Auth(u,r,a,c))` | Аутентификация |
| A2 | `inj-event(Server_Finish_Tr(tr)) ==> inj-event(Authnr_Finish_Tr(tr))` | Транзакции |

Полные типизированные кванторы находятся в исходнике. Для A5 комментарий обещает соглашение по большему набору данных, чем реально передаётся в Client_Init_Reg (только u,r); это существенное ограничение интерпретации. `PinToken` действительно существует: FIDO2.pvl / CTAP_Authnr, строка 232; таблицы Authnr_Token/Client_Token, 187–188. В шаблонах есть одноимённый локальный fresh name; привязку `query secret PinToken` и достижимость выбранных ветвей необходимо проверить при первом запуске, не объявляя заранее ни ошибкой, ни корректным доказательством.

Секретность PIN (C7 статьи) в списке AllQueries отсутствует. A0 — общее обозначение статьи, отдельного Query('A0') нет. A3/A4 не являются переключателями Python: в Auth_A3_A4.pv проверяется correspondence A1 в специальной конфигурации утечек. Unlinkability задаётся `choice`, а не обычным secrecy query: Reg_unlink.pv:48, Auth_unlink.pv:58.

## 6. Каналы, криптография и атакующий

FILE: FIDO2.pvl; REGION: 22–68 (симметричное шифрование, hash/HMAC, подписи, символическое DH); 174–176 (cP public, CR и CA private), 187–205 (таблицы и константы), 212–224 (события), 230–370 (CTAP роли).

Это символическая модель с идеализированными криптографическими примитивами. Активный нарушитель контролирует публичный канал. Контроль приватных каналов между честными ролями не предполагается; дополнительные публичные сеансы задаёт Python. Криптоанализ, brute-force PIN, время выполнения, ошибки устройств и реальная browser UX моделью автоматически не покрываются.

## 7. Вызов ProVerif и результаты

FILE: FIDO2Verif.py; REGION: Case.proverif (545–571), analysis (788–846), Setting (42–67).

Фактический запуск: `Popen('proverif -lib ' + Setting.LibPath + ' ' + self.query_path, stdout=PIPE, stderr=PIPE)`; строка, shell=False, timeout 30 секунд через Timer/kill. На POSIX строка с пробелами трактуется как одно имя executable, поэтому этот вызов требует платформенной адаптации надстройкой. Директория executable не равна PATH: просто положить exe рядом недостаточно для всех ОС/конфигураций.

Артефакты: TEMP/TEMP-…pv (обычно удаляется после проверки), LOG-файлы, Result/phase/ctap/type/query/… . Пути LOG используют Windows backslash. Шаблон имени TEMP не включает ctap_type. Result сохраняет модель и только хвост вывода, а не полноценные raw stdout/stderr/exit code.

Ограничения:

1. Setting при **определении класса** удаляет LOG, TEMP, Result: запуск `-h` и импорт тоже модифицируют cwd. Main дополнительно открывает восемь логов до разбора CLI.
2. `if result.find(b'a trace has been found.'):` и аналогичный find('trace') трактуют -1 как True, 0 как False; отсутствие маркера может дать ложный ret='false'. Не использовать эти статусы как собственные результаты.
3. returncode и stderr не анализируются; timeout не надёжно отделён от других исходов; обрезание stdout и поиск слов не заменяют разбор RESULT.
4. `if ret != 'false'` сохраняет также неизвестные/ошибочные случаи, хотя комментарий обещает только true.
5. Auth_A3_A4.pv:98–120 передаёт токен дополнительным аргументом в CTAP_Authnr/Auth_Authnr и опускает ctap_type в некоторых ролях; текущие сигнатуры FIDO2.pvl:230,497,650 другие. До исправления отдельной копии это плохой baseline.
6. Вложенный zip не эквивалентен рабочему дереву: после нормализации CRLF Python и PV совпадают, но в FIDO2.pvl архива строка Constant Declaration заканчивается `)` вместо `*)`. Смешивать библиотеку из zip с корневыми моделями нельзя.
7. Нет подтверждённых экспериментальных результатов в текущем отчёте; исходные комментарии и ожидания ими не являются.

## 8. Минимальный baseline

Предпочтителен документированный прямой запуск из корня чистой рабочей копии:

```sh
proverif -lib "FIDO2.pvl" Reg_unlink.pv
```

FILE: README.md; REGION: Verify the unlinkability goals. Параметры уже заданы: ctap_type=getToken, au_type=client, CA/CR private, без добавленных утечек. Проверяется biprocess с различием wrapping key. Ожидание из статьи: P1 удовлетворяется (раздел 5.1 / Privacy Properties), **не результат текущего запуска**. Не подменять это проверкой secret PinToken.

Статус: NOT RUN — отсутствует нативный ProVerif. Команда существует в первоисточнике; её успешность и длительность пока не подтверждены. До начала матрицы нужен raw лог и точный RESULT. `python FIDO2Verif.py -s -t reg_client` — реальная команда, но пакетный анализ и потому не один минимальный baseline.
