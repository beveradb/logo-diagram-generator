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
    "#6495ed",
    "yellow",
]


def override_config(config, override_configs):
    """
    Overrides the original configuration with values from the list of override configurations.
    Supports overriding both scalar values and lists.
    :param config: The original configuration dictionary.
    :param override_configs: A list of override configuration dictionaries.
    :return: The updated configuration dictionary.
    """

    def apply_override(config, key_path, value):
        """
        Recursively apply an override value based on a list of keys indicating the path.
        Supports overriding lists by detecting a delimiter in the value.
        :param config: The configuration dictionary to update.
        :param key_path: The list of keys indicating the path to the value to override.
        :param value: The override value.
        """
        key = key_path[0]
        if len(key_path) == 1:
            if "," in value and (key not in config or isinstance(config.get(key, ""), list)):
                # If the value contains a comma and either the key isn't found in the config or the target is a list,
                # assume this config entry is supposed to be a list and split the value.
                value = value.split(",")
            if key in config:
                logging.info(f"Overriding value of key {key} from {config[key]} to {value}")
            else:
                logging.info(f"Key {key} not found in the original config. Adding it with value: {value}")
            config[key] = value
        else:
            if key not in config or not isinstance(config[key], dict):
                logging.info(f"Creating nested config for key {key} to accommodate override.")
                config[key] = {}
            apply_override(config[key], key_path[1:], value)

    for override_config in override_configs:
        for key, value in override_config.items():
            key_path = key.split(".")
            apply_override(config, key_path, value)

    return config


def update_config(config_filepath, tool_name, updates):
    """
    Updates the configuration file with the given updates for the specified tool.
    :param config_filepath: Path to the configuration file.
    :param tool_name: Name of the tool to update.
    :param updates: Dictionary of updates to apply.
    """
    logging.debug(f"Updating config file {config_filepath} for tool {tool_name} with updates: {updates}")

    with open(config_filepath, "r") as file:
        config = yaml.safe_load(file)

    updated = False
    if "centralTool" in config["ecosystem"] and config["ecosystem"]["centralTool"].get("name") == tool_name:
        config["ecosystem"]["centralTool"].update(updates)
        updated = True
        logging.info(f"Successfully updated central tool in config file with new values: {updates}")
    else:
        for category in config["ecosystem"]["groups"]:
            for tool in category.get("tools", []):
                if tool.get("name") == tool_name:
                    tool.update(updates)
                    updated = True
                    logging.info(f"Successfully updated tool {tool_name} in config file with new values: {updates}")
                    break
            if updated:
                break

    if updated:
        with open(config_filepath, "w") as file:
            yaml.safe_dump(config, file)
            logging.info(f"Successfully wrote updated YAML back to config file: {config_filepath}")
    else:
        logging.error(f"Failed to update config file for tool {tool_name} with updates: {updates}")


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
