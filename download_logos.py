import os
import requests
import yaml
from urllib.parse import urlparse
import logging


def configure_logging():
    """
    Configures the logging system, setting the level and format for log messages.
    """
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def update_config(config_path, tool_name, updates):
    """
    Updates the configuration file with the given updates for the specified tool.
    :param config_path: Path to the configuration file.
    :param tool_name: Name of the tool to update.
    :param updates: Dictionary of updates to apply.
    """
    with open(config_path, "r") as file:
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
        with open(config_path, "w") as file:
            yaml.safe_dump(config, file)


# Function to sanitize tool names, labels, and aliases for URL
def sanitize_for_url(text):
    return "".join(
        char.lower() if char.isalnum() or char == " " or char == "_" else ""
        for char in text
    ).replace(" ", "_")


def generate_vectorlogozone_urls(tool_config):
    """
    Generate a list of URLs to attempt to download the SVG logo from.
    :param tool_config: The config dict for the tool.
    :return: A list of URLs to try.
    """

    urls_to_try = []

    tool_name = tool_config.get("name", None)
    if tool_name is not None:
        tool_name_slug = sanitize_for_url(tool_name)
        urls_to_try.append(
            f"https://www.vectorlogo.zone/logos/{tool_name_slug}/{tool_name_slug}-ar21.svg"
        )

    tool_alias = tool_config.get("alias", None)
    if tool_alias is not None:
        tool_alias_slug = sanitize_for_url(tool_alias)
        urls_to_try.append(
            f"https://www.vectorlogo.zone/logos/{tool_alias_slug}/{tool_alias_slug}-ar21.svg"
        )

    tool_label = tool_config.get("label", None)
    if tool_label is not None:
        tool_label_slug = sanitize_for_url(tool_label)
        urls_to_try.append(
            f"https://www.vectorlogo.zone/logos/{tool_label_slug}/{tool_label_slug}-ar21.svg"
        )

    return urls_to_try


def handle_logo_not_found(tool_name, output_path):
    """
    Handles cases where the logo cannot be found automatically.
    Prompts the user for alternative actions.
    :param tool_name: The name of the tool.
    :param output_path: The path where the logo should be saved.
    """
    logging.warning(f"Could not find a logo for {tool_name}.")
    vectorlogozone_search_url = f"https://www.vectorlogo.zone/?q={tool_name}"
    logging.info(f"Try searching VectorLogoZone first: {vectorlogozone_search_url}")
    found_with_alias = (
        input(
            "Did you find the logo with a slightly different name in the URL bar? (y/n): "
        )
        .strip()
        .lower()
    )

    if found_with_alias == "y":
        alias = input("Enter the alias name found in the VectorLogoZone URL: ").strip()
        # Update the alias in config.yml
        update_config(config_path, tool_name, {"alias": alias})

        # Attempt to download the logo using the new alias
        download_svg(tool_name, tool_name, alias, output_path)
    elif found_with_alias == "n":
        search_url = f"https://logosear.ch/search.html?q={tool_name}"
        logging.info(f"Try searching for one online, e.g. here: {search_url}")

        user_url = input("Once you find an SVG URL for your tool, enter the URL here: ")
        if user_url:
            # Update the svgURL in config.yml
            update_config(config_path, tool_name, {"svgURL": user_url})

            # Attempt to download the logo using the user-provided URL
            download_svg(tool_name, tool_name, None, output_path)
        else:
            logging.info("No URL provided. Skipping download.")


def download_svg(tool_config, output_dir):
    """
    Attempt to download an SVG logo for the given tool
    Test various URLs (using the tool name, label or alias) to find a working URL.
    If all attempts fail, prompt the user for an alternative URL.
    If the logo already exists at the output path, do not download it again.
    """

    tool_name = tool_config.get("name")
    tool_name_slug = sanitize_for_url(tool_name)
    output_path = os.path.join(output_dir, f"{tool_name_slug}.svg")

    # Check if the logo already exists
    if os.path.exists(output_path):
        logging.info(f"Logo for {tool_name} already exists. Skipping download.")
        return

    urls_to_try = generate_vectorlogozone_urls(tool_config)

    # If svgURL is in the config for this tool, insert at the top of urls_to_try to try this first!
    tool_svg_url = tool_config.get("svgURL", None)
    if tool_svg_url is not None:
        urls_to_try.insert(0, tool_svg_url)

    for url in urls_to_try:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logging.info(f"Downloaded VectorLogoZone logo for {tool_name}.")
                return
            else:
                logging.warning(
                    f"Failed to download logo from {url}. Status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading logo from {url}: {e}")

    # If we reach this point, the logo was not found on VectorLogoZone using the name or alias
    handle_logo_not_found(tool_name, output_path)


def ensure_directory_exists(directory_path):
    """
    Ensures that the specified directory exists. If not, it creates the directory.
    :param directory_path: The path to the directory to check and potentially create.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)


def load_config(config_path="config.yml"):
    """
    Loads the YAML configuration from the given path.
    :param config_path: Path to the YAML configuration file.
    :return: The loaded configuration dictionary.
    """
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config


def main():
    ensure_directory_exists("logos")
    config = load_config()
    ecosystem = config.get("ecosystem", {})
    tools = []

    central_tool = ecosystem.get("centralTool", {})
    if central_tool.get("name"):
        tools.append(central_tool)

    for group in ecosystem.get("groups", []):
        for tool in group.get("tools", []):
            tools.append(tool)

    for tool_config in tools:
        download_svg(tool_config, output_dir="logos")


if __name__ == "__main__":
    configure_logging()
    main()
