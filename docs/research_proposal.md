# Экспериментальная тема и план

GENERATED DRAFT на основе проверенных исходников · 14.11.2026.

Основная тема пользователя сохраняется: **«Разработка программных средств для экспериментального анализа безопасности протокола FIDO2 на основе FIDO2Verif»**.

Рекомендуемая точная экспериментальная подтема: **«Влияние дополнительных сеансов с публичными интерфейсами клиента на секретность PinToken и инъективную аутентификацию в модели FIDO2Verif»**.

Обоснование: S-pintok, A6, A1, getToken, RegEntities/AuthEntities действительно присутствуют. Слово «компрометация» в описании работы нужно раскрыть как конкретную добавленную роль с cP, а не полный захват ОС/устройства. Объект — историческая символическая модель; предмет — зависимость результатов queries от добавленных сеансов. Метод — controlled comparison при фиксированных ctap_type/getToken и au_type/client.

## Минимальный baseline

Отдельная нулевая проверка, не часть матрицы: `proverif -lib "FIDO2.pvl" Reg_unlink.pv`, cwd upstream working copy. P1/getToken/client. Ожидание из статьи §5.1 — выполняется. Статус **NOT RUN**: ProVerif пока отсутствует. Успех не объявлен; журнал baseline_reproduction.md не выдаётся за отчёт успешного воспроизведения.

## Предлагаемая матрица: 12 основных запусков

Зафиксировать upstream commit из provenance.json, ProVerif version, библиотеку, ctap_type=getToken, au_type=client, нулевые утечки полей. Для auth_client_em: tr_type=empty. Сохранять исходную репликацию, не использовать предварительное удаление `!` как окончательный результат. Каждая строка — один input с одним query и одним запуском ProVerif.

Наборы entities — индексы **обычных** RegEntities/AuthEntities, не V2:

- E0: пустой набор, только исходные честные роли.
- E1: `{1}` — дополнительный клиент с CA=cP; upstream Case.write_file также добавляет CTAP_Client на cP. Это единый предусмотренный upstream случай; изменение включает CTAP и WebAuthn сеансы, их эффекты не разделены.
- E2: `{2}` — дополнительный клиент с CR=cP и CA=CA; отдельного CTAP_Client на cP не добавляет.

| ID | Upstream scenario | Changed assumption | Checked property | Expected comparison | Actual result | Runtime |
|---|---|---|---|---|---|---|
| R01 | reg_client/getToken | E0 | S-pintok | Опорное значение C8 | NOT RUN | null |
| R02 | reg_client/getToken | E1 | S-pintok | С R01; ожидаем влияние публичного клиентского сеанса к FA | NOT RUN | null |
| R03 | reg_client/getToken | E2 | S-pintok | С R01/R02; проверить специфичность эффекта | NOT RUN | null |
| R04 | reg_client/getToken | E0 | A6 | Опорный correspondence | NOT RUN | null |
| R05 | reg_client/getToken | E1 | A6 | С R04; secrecy и agreement могут различаться | NOT RUN | null |
| R06 | reg_client/getToken | E2 | A6 | С R04/R05, без заранее назначенного результата | NOT RUN | null |
| R07 | auth_client_em/getToken | E0 | S-pintok | Опорное значение C8 в аутентификации | NOT RUN | null |
| R08 | auth_client_em/getToken | E1 | S-pintok | С R07; сопоставить с R02 | NOT RUN | null |
| R09 | auth_client_em/getToken | E2 | S-pintok | С R07/R08; сопоставить с R03 | NOT RUN | null |
| R10 | auth_client_em/getToken | E0 | A1 | Опорный correspondence | NOT RUN | null |
| R11 | auth_client_em/getToken | E1 | A1 | С R10; сопоставить с R05 | NOT RUN | null |
| R12 | auth_client_em/getToken | E2 | A1 | С R10/R11; сопоставить с R06 | NOT RUN | null |

Descriptions задаются комбинацией scenario/assumption/query выше. Это план, не выполненные experiments/configs и не новый CLI. Сначала подтвердить, что `query secret PinToken` относится к токену CTAP_Authnr. Если возникают ambiguity/unreachable ветви, остановить интерпретацию и описать минимальное изменение отдельной копии; не молча переименовывать переменные. Для correspondence нужны дополнительные диагностические проверки достижимости finish events; они не входят в 12 основных измерений, их число и результаты фиксировать отдельно. Бюджет baseline+матрица+диагностика должен остаться в пределах 24 запусков; timeout не считать false.

## Собственная работа студента и вклад авторов

Авторам принадлежат историческая модель, сообщения, криптографические абстракции, исходные security queries, наборы дополнительных ролей, подход поиска минимальных assumptions и опубликованные выводы. Собственный вклад будущего КП: безопасная изоляция запусков, конфигурация небольшой явной матрицы, сохранение provenance/stdout/stderr/returncode/runtime, проверяемый parser RESULT, таблицы сравнения, тесты собственного кода, самостоятельная интерпретация и gap analysis. Это инженерный и воспроизводящий вклад, а не заявленная новая атака или новая модель FIDO2.

## Что требует решения до реализации

1. Зафиксировать доступный commit вместо недоступного paper tag; не утверждать точную идентичность paper artifact.
2. Установить нативный ProVerif и записать реальную версию; исходное требование 2.01+, официальный install page предлагает 2.05.
3. Выполнить baseline с полным raw output; сверить P1 со статьёй.
4. Проверить token query, event reachability и точное сопоставление assumptions статьи.
5. Уточнить факультет/кафедру и применимую методичку. Тема и научные выводы подлежат проверке руководителем.
6. После одобрения отчёта реализовать надстройку. Это явная граница из последнего блока задания пользователя: «Не начинай писать experiment manager, пока я не одобрю этот отчёт».
