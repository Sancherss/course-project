# Воспроизводимое окружение

VERIFIED EXPERIMENTALLY: Linux x86_64/glibc 2.41, Python 3.12.14, OCaml 4.14.2, ProVerif 2.05. Виртуальное окружение `.venv`; локальный verifier `.tools/proverif/proverif`. Публичный bootstrap требует POSIX shell, curl, sha256sum, tar, gcc и make; его команды соответствуют выполненной source-сборке. Точный текущий статус — evidence/environment.json.

## Версии и установка

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
./scripts/bootstrap_proverif.sh
.venv/bin/python scripts/check_environment.py
```

bootstrap проверяет SHA256 загружаемых архивов по scripts/toolchain.sha256. Сборка не требует root, не изменяет глобальную конфигурацию и занимает несколько минут. Для уже установленного нативного verifier можно задать `PROVERIF=/absolute/path/to/proverif` или использовать `--proverif` в CLI и baseline-скрипте. Требование upstream 2.01+; собственная надстройка требует Python 3.10+.

ProVerif version получается реальной опцией `-help`, не вымышленным `--version`. Вызов `-set preciseActions true` используется только в отдельной precision.yaml после проверки официального manual и source. Upstream Windows proverif.exe не запускается и не переименовывается в Linux binary. Docker не нужен для текущего варианта. Нативная Windows-совместимость Python-надстройки не проверена; для Windows рекомендуется воспроизведение в Linux/WSL с отдельной проверкой окружения.

## Исходники

Git submodule upstream/FIDO2Verif закреплён на commit `2d8eaf326117bd7e4706c48b2d24e27b4a006fa6`. При новом clone проекта выполнить `git submodule update --init`. Без внешнего remote родительского проекта можно распаковать подготовленный архив: он содержит исходное дерево и локальную Git-историю. Статус чистоты и commit проверяются до каждого основного запуска.

## Происхождение сборки текущего сеанса

OCaml был собран в соседнем рабочем каталоге `/workspace/work/ocaml-local`, затем официальный build ProVerif выполнен с этим toolchain; полученный нативный binary скопирован в `.tools/proverif/proverif`. Bootstrap размещает эквивалентные source/build каталоги внутри `.tools`; пути сборки не следует принимать за обязательные пути на другом компьютере. Не обещается byte-for-byte идентичность binary между разными ОС/компиляторами; сохраняются его фактический SHA256 и версия.

Raw metadata содержит время UTC; для показа пользователю можно преобразовать в Europe/Minsk. Длительности измеряются монотонными часами. Прогоны разных серий в этом сеансе частично пересекались по времени; это не performance benchmark и не основание сравнивать небольшие различия runtime.

## Экспорт и архив

requirements.txt фиксирует также matplotlib 3.10.1 для экспорта PNG/SVG. `make report` воспроизводит рисунок из final snapshot и создаёт DOCX. В полном архиве вложены нативный Linux verifier, его GPL LICENSE и официальный source tarball; переносимый способ установки — bootstrap. Полные сборочные каталоги OCaml и виртуальное окружение не включаются.
