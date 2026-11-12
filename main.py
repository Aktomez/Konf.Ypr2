import sys
import os
import json
import urllib.request
import urllib.error
import yaml


def load_config(config_path="config.yaml"):
    """Загрузка и валидация конфигурационного YAML-файла."""
    if not os.path.exists(config_path):
        print(f"Ошибка: Конфигурационный файл '{config_path}' не найден.", file=sys.stderr)
        sys.exit(1)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"Ошибка при разборе YAML-файла: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(config, dict):
        print("Ошибка: Корневой элемент конфигурации должен быть словарем.", file=sys.stderr)
        sys.exit(1)

    required_keys = [
        "package_name",
        "repository_url",
        "test_mode",
        "test_repo_path",
        "output_image",
        "ascii_tree"
    ]

    for key in required_keys:
        if key not in config:
            print(f"Ошибка: В конфигурационном файле отсутствует обязательный параметр '{key}'.", file=sys.stderr)
            sys.exit(1)

    return config


def fetch_rust_dependencies(package_name, base_url):
    """Получение прямых зависимостей пакета Rust через API crates.io."""
    base_url = base_url.rstrip("/")
    url = f"{base_url}/{package_name}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DependencyVisualizerStudentProject (educational)"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    versions = data.get("versions", [])
    if not versions:
        return []

    latest_version = None
    for v in versions:
        if not v.get("yanked", False):
            latest_version = v.get("num")
            break
    if not latest_version and versions:
        latest_version = versions[0].get("num")

    if not latest_version:
        return []

    deps_url = f"{base_url}/{package_name}/{latest_version}/dependencies"
    req_deps = urllib.request.Request(
        deps_url,
        headers={"User-Agent": "DependencyVisualizerStudentProject (educational)"}
    )

    try:
        with urllib.request.urlopen(req_deps) as response:
            deps_data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []

    dependencies = []
    for dep in deps_data.get("dependencies", []):
        kind = dep.get("kind")
        if kind is None or kind == "normal":
            dep_name = dep.get("crate_id")
            if dep_name:
                dependencies.append(dep_name)

    return dependencies


def load_test_graph(file_path):
    """Загрузка графа из тестового файла (пары вершин, например, A B)."""
    graph = {}
    if not os.path.exists(file_path):
        print(f"Ошибка: Тестовый файл графа '{file_path}' не найден.", file=sys.stderr)
        return graph

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                u, v = parts[0], parts[1]
                graph.setdefault(u, []).append(v)
    return graph


def build_dependency_graph(start_package, base_url, test_mode, test_repo_path):
    """Построение полного транзитивного графа зависимостей с помощью DFS."""
    graph = {}

    if test_mode:
        print(f"Загрузка графа из тестового файла: {test_repo_path}")
        raw_graph = load_test_graph(test_repo_path)
        visited = set()

        def dfs_test(node):
            if node in visited:
                return
            visited.add(node)
            neighbors = raw_graph.get(node, [])
            graph[node] = neighbors
            for neighbor in neighbors:
                dfs_test(neighbor)

        if start_package in raw_graph or any(start_package in v_list for v_list in raw_graph.values()):
            dfs_test(start_package)
        else:
            print(f"Предупреждение: Корневой узел '{start_package}' не найден в тестовом графе.")

    else:
        visited = set()

        def dfs_crates(package):
            if package in visited:
                return
            visited.add(package)
            print(f"Запрос зависимостей для: {package}")
            deps = fetch_rust_dependencies(package, base_url)
            graph[package] = deps
            for dep in deps:
                dfs_crates(dep)

        dfs_crates(start_package)

    return graph


def print_ascii_tree(graph, root, prefix=""):
    """Печать дерева зависимостей в формате ASCII."""
    print(f"{prefix}{root}")
    children = graph.get(root, [])
    for i, child in enumerate(children):
        connector = "└── " if i == len(children) - 1 else "├── "
        extension = "    " if i == len(children) - 1 else "│   "
        if child in graph and prefix.count(child) < 1:
            print_ascii_tree(graph, child, prefix + extension)
        else:
            print(f"{prefix}{extension}{connector}{child} (already visited)")


def get_load_order(graph, root):
    """Определение порядка загрузки зависимостей (Этап 4)."""
    visited = set()
    order = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor)
        order.append(node)

    if root in graph:
        dfs(root)
    return order


def generate_plantuml_graph(graph, output_path):
    """Генерация текстового представления графа на языке PlantUML (Этап 5)."""
    puml_content = "@startuml\n"
    puml_content += "skinparam nodeStyle rectangle\n"
    for parent, children in graph.items():
        if not children:
            puml_content += f"\"{parent}\"\n"
        for child in children:
            puml_content += f"\"{parent}\" --> \"{child}\"\n"
    puml_content += "@enduml\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(puml_content)
    print(f"PlantUML граф успешно сохранен в: {output_path}")


def main():
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    config = load_config(config_path)

    print("=== Параметры конфигурации ===")
    for key, value in config.items():
        print(f"{key}: {value}")
    print("-" * 30)

    package_name = config["package_name"]
    repo_url = config["repository_url"]
    test_mode = config["test_mode"]
    test_repo_path = config["test_repo_path"]
    output_image = config["output_image"]
    ascii_tree_enabled = config["ascii_tree"]

    print(f"Построение графа для '{package_name}'...")
    graph = build_dependency_graph(package_name, repo_url, test_mode, test_repo_path)

    if ascii_tree_enabled and package_name in graph:
        print("\n--- Дерево зависимостей (ASCII) ---")
        print_ascii_tree(graph, package_name)
        print("-" * 30)

    print("\n--- Порядок загрузки зависимостей (Этап 4) ---")
    load_order = get_load_order(graph, package_name)
    print(" -> ".join(load_order))
    print("-" * 30)

    if output_image:
        generate_plantuml_graph(graph, output_image)


if __name__ == "__main__":
    main()