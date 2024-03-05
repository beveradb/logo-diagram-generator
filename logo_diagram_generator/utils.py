import os
import string
import logging
import yaml

visually_distinct_colors = [
    "darkgreen",
    "darkblue",
    "maroon3",
    "red",
    "burlywood",
    "lime",
    "aqua",
    "fuchsia",
    "cornflower",
    "yellow",
]


def update_config(config_filepath, tool_name, updates):
    """
    Updates the configuration file with the given updates for the specified tool.
    :param config_filepath: Path to the configuration file.
    :param tool_name: Name of the tool to update.
    :param updates: Dictionary of updates to apply.
    """
    with open(config_filepath, "r") as file:
        config = yaml.safe_load(file)

    updated = False
    if "centralTool" in config and config["centralTool"].get("name") == tool_name:
        config["centralTool"].update(updates)
        updated = True
    else:
        for category in config.get("ecosystem", []):
            for tool in category.get("tools", []):
                if tool.get("name") == tool_name:
                    tool.update(updates)
                    updated = True
                    break
            if updated:
                break

    if updated:
        with open(config_filepath, "w") as file:
            yaml.safe_dump(config, file)


def slugify(text):
    logging.debug(f"Generating filesystem and URL safe slug for input text: {text}")
    allowed_chars = string.ascii_letters + string.digits + " _-."
    slug = "".join(char.lower() if char in allowed_chars else "" for char in text).replace(" ", "_")
    logging.debug(f"Returning slug: {slug}")
    return slug


def ensure_directory_exists(directory_path):
    """
    Ensures that the specified directory exists. If not, it creates the directory.
    :param directory_path: The path to the directory to check and potentially create.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def read_config(config_filepath):
    logging.debug(f"Reading configuration from {config_filepath}")
    with open(config_filepath, "r") as file:
        return yaml.safe_load(file)
