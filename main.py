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
    """
    Получение прямых зависимостей пакета Rust через API crates.io (Этап 2).
    """
    base_url = base_url.rstrip("/")
    url = f"{base_url}/{package_name}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "DependencyVisualizerStudentProject (educational)"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Ошибка HTTP при запросе к реестру для пакета '{package_name}': {e.code}", file=sys.stderr)
        return []
    except urllib.error.URLError as e:
        print(f"Ошибка сети при подключении к '{url}': {e.reason}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print("Ошибка: Не удалось разобрать JSON-ответ от сервера.", file=sys.stderr)
        return []

    versions = data.get("versions", [])
    if not versions:
        print(f"Предупреждение: У пакета '{package_name}' не найдено версий.")
        return []

    # Берем первую стабильную или доступную версию
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
    except Exception as e:
        print(f"Ошибка при получении зависимостей версии {latest_version}: {e}", file=sys.stderr)
        return []

    dependencies = []
    for dep in deps_data.get("dependencies", []):
        kind = dep.get("kind")
        if kind is None or kind == "normal":
            dep_name = dep.get("crate_id")
            if dep_name:
                dependencies.append(dep_name)

    return dependencies


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

    print(f"Сбор прямых зависимостей для пакета '{package_name}' (Этап 2)...")
    dependencies = fetch_rust_dependencies(package_name, repo_url)

    print(f"\nПрямые зависимости пакета '{package_name}':")
    if dependencies:
        for dep in dependencies:
            print(f" - {dep}")
    else:
        print(" (Зависимости не найдены или произошла ошибка при запросе)")


if __name__ == "__main__":
    main()