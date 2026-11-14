# Статья ESORICS 2022: конспект и соответствие коду

VERIFIED FROM SOURCE · 14.11.2026. Не экспериментальные результаты этого проекта.

Jingjing Guan, Hui Li, Haisong Ye, Ziming Zhao. A Formal Analysis of the FIDO2 Protocols. ESORICS 2022, LNCS 13556, pp. 3–21. DOI подтверждён первой страницей PDF: https://doi.org/10.1007/978-3-031-17143-7_1 . Авторская копия: https://cactilab.github.io/assets/pdf/jingjing2022fido2.pdf ; связана с GitHub на https://cactilab.github.io/publications/ .

## Что исследовали авторы

Разделы 2, 4.1: CTAP2 и WebAuthn рассматриваются совместно. 4 варианта CTAPType × 2 варианта AuType дают 8 сценариев регистрации; ещё × 3 TrType дают 24 сценария аутентификации/транзакций. Client/server относятся к хранению ключа credential. Это не классификация passkeys по синхронизации.

Раздел 3.1: идеальная криптография; каналы IPC FC–FA и TLS FC–RP между честными участниками конфиденциальны и целостны. Нарушитель может создавать сеансы через контролируемые сущности и получать их данные. Общедоступны идентификаторы, публичные ключи и G; допускаются выбранные компрометации данных. Это уточнённая модель угроз, не безусловная безопасность реальных систем.

Таблица 4 и раздел 3.2:

- C1 wrapping key, C2 attestation private key, C3 credential private key, C4 counter, C5 credential ID, C6 transaction data, C7 current/new PIN, C8 PinToken — секретность.
- A1 injective agreement RP с authenticator по данным аутентификации; A2 по транзакции; A3 verifier leak resilience; A4 authenticator leak resilience; A5 user consent; A6 attestable properties. A0 — обобщённое требование injective agreement.
- P1 unlinkability между процессами одного пользователя на разных RP; моделируется эквивалентностью, а не обычным attacker query.

Раздел 5: FIDO2Verif генерирует комбинации типов, утечек и дополнительных ролей и ищет минимальные предположения. Статья сообщает 78 336 test cases; это число авторов, не число запусков нашего пакета. Нельзя приравнивать количество потенциальных случаев к фактически вызванным процессам ProVerif: код использует пропуски подмножеств и двухэтапную проверку.

## Результаты авторов и пределы переноса

Раздел 5.1, таблицы 5–6: минимальные предположения о данных и участниках зависят от свойства и фазы; PinToken (C8) зависит от ограничения malicious client к authenticator (¬C[A]); P1 авторы считают выполненным в регистрации и аутентификации. Таблицы в PDF содержат символы, плохо извлекаемые pdftotext: для точного переноса логических формул следует сверять визуально с PDF, а не угадывать по повреждённому тексту.

Раздел 5.2: авторы описывают MITM при неаутентифицированном ECDH CTAP2, authenticator rebinding, parallel session attack, раскрытие персональных данных (counter/transaction). Это результаты их предположений и модели 2022 года. Мы не подтвердили эти атаки собственным запуском и не переносим их на современные спецификации.

Раздел 5.3: рекомендации — явная модель компрометации, взаимная проверка FA/FC и связь CTAP-сеанса с последующей операцией, аутентификация клиента на RP, защита персональных данных дополнительным шифрованием с использованием ECIES-подобного механизма. Не заявляем, что эти исправления реализованы или формально перепроверены в доступном upstream.

## Утверждение → код

Все FILE относительно upstream/FIDO2Verif; строки для commit из provenance.json.

| Утверждение статьи | FILE / LINE/REGION | Статус |
|---|---|---|
| 32 комбинации типов, §4.1 | FIDO2Verif.py / AllCTAPType и Types, 144–198; FIDO2.pvl / 195–205 | VERIFIED FROM SOURCE |
| C8, секретность токена | FIDO2Verif.py / AllQueries:211; FIDO2.pvl / CTAP_Authnr:232, таблицы 187–188 | Запрос найден; привязка имени и результат NOT VERIFIED |
| C1/C2/C3/C4/C5 | FIDO2Verif.py / AllQueries и subclasses, 211–255 | Имена запросов подтверждены; каждый контекст нужно сверить |
| C6 | FIDO2Verif.py / AuthClientTrQueries:285, AuthServerTrQueries:306 | Tr/tr различаются; результат NOT VERIFIED |
| C7 | AllQueries и subclasses | NOT VERIFIED: запроса PIN в генераторе не найдено |
| A1/A2/A5/A6 | FIDO2Verif.py / 235–240, 271–311 | Найдены; A5 Client_Init_Reg передаёт только u,r, не весь набор таблицы 4 |
| A3/A4, три группы сеансов, §4.2 | Auth_A3_A4.pv / process 4–121 | Сценарий найден; вызовы не согласованы с текущими сигнатурами библиотеки; результат NOT VERIFIED |
| P1 | Reg_unlink.pv:48, Auth_unlink.pv:58 | Biprocess найден; результат NOT VERIFIED |
| Поиск минимальных assumptions | FIDO2Verif.py / Generator.reverse_f_e, jump_if_its_secure, analysis | Алгоритм найден; корректность всех отсечений не доказана |
| 78 336 cases | Статья §5; Generator и analysis | Не воспроизведено; нет готового независимого лога |
| MITM, rebinding, parallel sessions | FIDO2.pvl / CTAP_* и Reg_*/Auth_*; дополнительные роли в RegEntities/AuthEntities | Механизмы модели найдены, соответствующие attack traces NOT VERIFIED |
| Исправления §5.3 | Отдельные исправленные модели не обнаружены | NOT VERIFIED |

## Что воспроизводить первым

1. P1 регистрации для getToken/client: команда `proverif -lib "FIDO2.pvl" Reg_unlink.pv`; ожидание true из §5.1. Это отдельный baseline эквивалентности.
2. C8 в getToken для reg_client и auth_client_em при отсутствии дополнительных ролей и при добавлении index 1 (клиент на публичном CA). Ожидание сравнительного эффекта по §5.1; точное соответствие исходной таблице требует результата и traces.
3. A6/A1 для тех же сеансов, чтобы сопоставить secrecy и correspondence. Перед выводом о выполненной аутентификации проверить достижимость finish event: true может быть вакуозным при невозможности завершить процесс.
