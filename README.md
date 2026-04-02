# DynSys Pro v8.5

Современная **научная программа** для анализа 2D нелинейных динамических систем:
- фазовые портреты;
- временные ряды;
- поиск точек равновесия;
- оценка устойчивости по Якобиану;
- приближённый показатель Ляпунова;
- экспорт траекторий в CSV.

## Запуск GUI

```bash
python dynsys_pro.py
```

## Запуск в консоли (CLI)

```bash
python dynsys_pro.py --cli --model "Стабильная любовь" --x0 0.2 --y0 0.4 --t-end 40 --points 500
```

Экспорт CSV в CLI:

```bash
python dynsys_pro.py --cli --model "Романтика" --export-csv out.csv
```

Список моделей:

```bash
python dynsys_pro.py --list-models
```

## Сборка EXE (Windows)

### Вариант 1: готовый скрипт

```bat
build_exe.bat
```

### Вариант 2: вручную

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm dynsys_pro.spec
```

Готовый файл: `dist/DynSysPro.exe`.

## Зависимости

См. `requirements.txt`.
