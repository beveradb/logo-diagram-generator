import os
import requests
import yaml
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Function to sanitize tool names, labels, and aliases for URL
def sanitize_for_url(text):
    return "".join(
        char.lower() if char.isalnum() or char == " " or char == "_" else ""
        for char in text
    ).replace(" ", "_")

def download_svg(tool_name, tool_label, tool_alias, output_path):
    """
    Attempt to download an SVG logo for the given tool name, label, or alias.
    If the download fails (404), try with the tool label, then the alias.
    If all attempts fail, prompt the user for an alternative URL.
    If the logo already exists at the output path, do not download it again.
    """

    # Check if the logo already exists
    if os.path.exists(output_path):
        logging.info(f"Logo for {tool_name} already exists. Skipping download.")
        return


    tool_name_sanitized = sanitize_for_url(tool_name)
    tool_label_sanitized = sanitize_for_url(tool_label)
    tool_alias_sanitized = sanitize_for_url(tool_alias) if tool_alias else None

    urls_to_try = []
    if tool_alias_sanitized:
        urls_to_try.append(
            f"https://www.vectorlogo.zone/logos/{tool_alias_sanitized}/{tool_alias_sanitized}-ar21.svg"
        )
    urls_to_try.extend(
        [
            f"https://www.vectorlogo.zone/logos/{tool_name_sanitized}/{tool_name_sanitized}-ar21.svg",
            f"https://www.vectorlogo.zone/logos/{tool_label_sanitized}/{tool_label_sanitized}-ar21.svg",
        ]
    )

    for url in urls_to_try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logging.info(f"Downloaded logo for {tool_name}.")
            return

    # If all URLs failed
    logging.warning(f"Could not find a logo for {tool_name}.")
    suggested_url = f"https://www.vectorlogo.zone/?q={tool_name_sanitized}"
    logging.info(f"Try searching here first: {suggested_url}")
    found_with_alias = (
        input("Did you find the logo with a slightly different name? (y/n): ")
        .strip()
        .lower()
    )

    if found_with_alias == "y":
        alias = input("Enter the alias name found on VectorLogoZone: ").strip()
        # Update the alias in config.yml
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        # Update the alias for the tool
        if "centralTool" in config and config["centralTool"].get("name") == tool_name:
            config["centralTool"]["alias"] = alias
        else:
            for category in config.get("ecosystem", []):
                for tool in category.get("tools", []):
                    if tool.get("name") == tool_name:
                        tool["alias"] = alias
                        break
        with open(config_path, "w") as file:
            yaml.safe_dump(config, file)
        # Download the logo using the new alias
        tool_alias_sanitized = sanitize_for_url(alias)
        url = f"https://www.vectorlogo.zone/logos/{tool_alias_sanitized}/{tool_alias_sanitized}-ar21.svg"
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logging.info(
                f"Downloaded logo for {tool_name} using alias from VectorLogoZone."
            )
        else:
            logging.error(f"Failed to download logo for {tool_name} using alias.")
    elif found_with_alias == "n":
        logging.info("Please search for the logo manually.")
        search_url = f"https://logosear.ch/search.html?q={tool_name_sanitized}"
        logging.info(f"Try searching for one online, e.g. here: {search_url}")
        user_url = input("Once you find an SVG URL for your tool, enter the URL here: ")
        if user_url:
            # Update the svgURL in config.yml
            with open(config_path, "r") as file:
                config = yaml.safe_load(file)
            # Update the svgURL for the tool
            if (
                "centralTool" in config
                and config["centralTool"].get("name") == tool_name
            ):
                config["centralTool"]["svgURL"] = user_url
            else:
                for category in config.get("ecosystem", []):
                    for tool in category.get("tools", []):
                        if tool.get("name") == tool_name:
                            tool["svgURL"] = user_url
                            break
            with open(config_path, "w") as file:
                yaml.safe_dump(config, file)
            # Download the logo using the user-provided URL
            response = requests.get(user_url)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logging.info(f"Downloaded logo for {tool_name} from user-provided URL.")
            else:
                logging.error(f"Failed to download logo from {user_url}.")
        else:
            logging.info("No URL provided. Skipping download.")


def main(config_path):
    # Ensure the logos directory exists
    if not os.path.exists("logos"):
        os.makedirs("logos")

    # Load the YAML configuration
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)

    # Process the central tool
    central_tool = config.get("centralTool", {})
    if central_tool.get("name"):
        tool_name_slug = sanitize_for_url(central_tool.get('name'))
        output_path = f"logos/{tool_name_slug}.svg"
        download_svg(
            central_tool.get("name"),
            central_tool.get("label", ""),
            central_tool.get("alias", ""),  # Extract alias
            output_path,
        )

    # Process each tool in the ecosystem
    for category in config.get("ecosystem", []):
        for tool in category.get("tools", []):
            tool_name = tool.get("name")
            tool_label = tool.get("label", "")
            tool_alias = tool.get("alias", "")  # Extract alias
            if tool_name:
                output_path = f"logos/{tool_name.lower()}.svg"
                download_svg(tool_name, tool_label, tool_alias, output_path)


if __name__ == "__main__":
    config_path = "config.yml"
    main(config_path)
