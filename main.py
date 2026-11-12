import sys
import os
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

    # Обязательные параметры по заданию Этапа 1
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


def main():
    config_path = "config.yaml"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    config = load_config(config_path)

    # Вывод всех настраиваемых параметров в формате ключ-значение (требование этапа 1)
    print("=== Параметры конфигурации (Этап 1) ===")
    for key, value in config.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()