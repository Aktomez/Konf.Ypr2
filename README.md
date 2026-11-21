# Konf.Ypr2 — Визуализатор зависимостей пакетов Rust

Утилита командной строки для построения графа зависимостей пакетов Rust
(через crates.io или локальный тестовый файл), вывода ASCII-дерева,
порядка загрузки зависимостей и генерации графа в формате PlantUML.

## Структура проекта

- `src/main.py` — основной модуль приложения
- `tests/test_visualizer.py` — модульные тесты
- `tests/test_graph.txt` — тестовый файл графа
- `config.yaml` — файл конфигурации
- `run.bat` / `run.sh` — скрипты запуска для Windows и Unix

## Запуск

- Windows: `run.bat`
- Linux / macOS: `./run.sh`
- Тесты: `python -m unittest discover -s tests`