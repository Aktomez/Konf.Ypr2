"""Визуализатор зависимостей пакетов Rust."""

import json
import os
import sys
import urllib.request
import yaml

SEPARATOR_WIDTH = 30
MIN_EDGE_PARTS = 2
REQUEST_TIMEOUT_SEC = 10
USER_AGENT = "DependencyVisualizerStudentProject (educational)"
REQUIRED_KEYS = [
    "package_name",
    "repository_url",
    "test_mode",
    "test_repo_path",
    "output_image",
    "ascii_tree",
]


def load_config(config_path="config.yaml"):
    """Загрузка и валидация конфигурационного YAML-файла."""
    if not os.path.exists(config_path):
        print(
            f"Ошибка: Конфигурационный файл '{config_path}' не найден.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as file_obj:
            config = yaml.safe_load(file_obj)
    except yaml.YAMLError as err:
        print(f"Ошибка при разборе YAML-файла: {err}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(config, dict):
        print(
            "Ошибка: Корневой элемент конфигурации должен быть словарем.",
            file=sys.stderr,
        )
        sys.exit(1)

    for key in REQUIRED_KEYS:
        if key not in config:
            print(
                f"Ошибка: Отсутствует обязательный параметр '{key}'.",
                file=sys.stderr,
            )
            sys.exit(1)

    return config


def _fetch_json(url):
    """Выполнение GET-запроса и декодирование JSON."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(
            req, timeout=REQUEST_TIMEOUT_SEC
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _pick_latest_version(versions):
    """Выбор актуальной не-yanked версии пакета."""
    for ver in versions:
        if not ver.get("yanked", False) and ver.get("num"):
            return ver.get("num")
    if versions:
        return versions[0].get("num")
    return None


def fetch_rust_dependencies(package_name, base_url):
    """Получение прямых зависимостей пакета Rust через API crates.io."""
    clean_url = base_url.rstrip("/")
    crate_data = _fetch_json(f"{clean_url}/{package_name}")
    if not isinstance(crate_data, dict):
        return []

    version = _pick_latest_version(crate_data.get("versions", []))
    if not version:
        return []

    deps_url = f"{clean_url}/{package_name}/{version}/dependencies"
    deps_data = _fetch_json(deps_url)
    if not isinstance(deps_data, dict):
        return []

    result = []
    for dep in deps_data.get("dependencies", []):
        kind = dep.get("kind")
        dep_name = dep.get("crate_id")
        if (kind is None or kind == "normal") and dep_name:
            result.append(dep_name)
    return result


def load_test_graph(file_path):
    """Загрузка графа из тестового файла (пары вершин, например A B)."""
    graph = {}
    if not os.path.exists(file_path):
        print(
            f"Ошибка: Тестовый файл графа '{file_path}' не найден.",
            file=sys.stderr,
        )
        return graph

    with open(file_path, "r", encoding="utf-8") as file_obj:
        for raw_line in file_obj:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= MIN_EDGE_PARTS:
                src, dst = parts[0], parts[1]
                graph.setdefault(src, []).append(dst)
    return graph


def _dfs_collect(node, get_neighbors, graph, visited):
    """Рекурсивный обход в глубину для построения графа."""
    if node in visited:
        return
    visited.add(node)