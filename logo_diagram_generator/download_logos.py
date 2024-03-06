import os
import logging
import requests

from logo_diagram_generator import utils


def generate_vectorlogozone_urls(tool_config):
    """
    Generate a list of URLs to attempt to download the SVG logo from.
    :param tool_config: The config dict for the tool.
    :return: A list of URLs to try.
    """

    urls_to_try = []

    tool_name = tool_config.get("name", None)
    if tool_name is not None:
        tool_name_slug = utils.slugify(tool_name)
        urls_to_try.append(f"https://www.vectorlogo.zone/logos/{tool_name_slug}/{tool_name_slug}-ar21.svg")

    tool_alias = tool_config.get("alias", None)
    if tool_alias is not None:
        tool_alias_slug = utils.slugify(tool_alias)
        urls_to_try.append(f"https://www.vectorlogo.zone/logos/{tool_alias_slug}/{tool_alias_slug}-ar21.svg")

    tool_label = tool_config.get("label", None)
    if tool_label is not None:
        tool_label_slug = utils.slugify(tool_label)
        urls_to_try.append(f"https://www.vectorlogo.zone/logos/{tool_label_slug}/{tool_label_slug}-ar21.svg")

    return urls_to_try


def handle_logo_not_found(config_filepath, tool_config, tool_name, logos_dir):
    """
    Handles cases where the logo cannot be found automatically.
    Prompts the user for alternative actions.
    :param tool_name: The name of the tool.
    :param logos_dir: The path where logos should be saved.
    """
    logging.warning(f"Could not find a logo for {tool_name}.")
    vectorlogozone_search_url = f"https://www.vectorlogo.zone/?q={tool_name}"
    logging.info(f"Try searching VectorLogoZone first: {vectorlogozone_search_url}")
    while True:
        found_with_alias = input("Did you find the logo with a slightly different name in the URL bar? (y/n): ").strip().lower()

        if found_with_alias == "y":
            alias = input("Enter the alias name found in the VectorLogoZone URL: ").strip()
            # Update the alias in config.yml
            utils.update_config(config_filepath, tool_name, {"alias": alias})
            tool_config = get_latest_config_for_tool(config_filepath, tool_name)
            # Attempt to download the logo using the new alias
            download_svg(config_filepath=config_filepath, tool_config=tool_config, logos_dir=logos_dir)
            break
        elif found_with_alias == "n":
            search_url = f"https://logosear.ch/search.html?q={tool_name}"
            logging.info(f"Try searching for one online, e.g. here: {search_url}")

            user_url = input("Once you find an SVG URL for your tool, enter the URL here: ")
            if user_url:
                # Update the svgURL in config.yml
                utils.update_config(config_filepath, tool_name, {"svgURL": user_url})
                tool_config = get_latest_config_for_tool(config_filepath, tool_name)

                # Attempt to download the logo using the user-provided URL now that has been saved to the config file
                download_svg(config_filepath=config_filepath, tool_config=tool_config, logos_dir=logos_dir)
            else:
                logging.info("No URL provided. Skipping download.")
            break
        else:
            logging.info("Invalid input. Please enter 'y' for yes or 'n' for no.")


def download_svg(config_filepath, tool_config, logos_dir):
    """
    Attempt to download an SVG logo for the given tool
    Test various URLs (using the tool name, label or alias) to find a working URL.
    If all attempts fail, prompt the user for an alternative URL.
    If the logo already exists at the output path, do not download it again.
    """

    tool_name = tool_config.get("name")
    tool_name_slug = utils.slugify(tool_name)
    output_path = os.path.join(logos_dir, f"{tool_name_slug}.svg")

    logging.debug(f"Download SVG called with tool_config: {tool_config}, logos_dir: {logos_dir}")

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
                logging.warning(f"Failed to download logo from {url}. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error downloading logo from {url}: {e}")

    # If we reach this point, the logo was not found on VectorLogoZone using the name or alias
    handle_logo_not_found(config_filepath=config_filepath, tool_config=tool_config, tool_name=tool_name, logos_dir=logos_dir)


def read_tools_from_config(config_filepath):
    logging.info(f"Reading configuration from file: {config_filepath}")
    config = utils.read_config(config_filepath)

    ecosystem = config.get("ecosystem", {})
    tools = []

    central_tool = ecosystem.get("centralTool", {})
    if central_tool.get("name"):
        tools.append(central_tool)

    for group in ecosystem.get("groups", []):
        for tool in group.get("tools", []):
            tools.append(tool)

    return tools


def get_latest_config_for_tool(config_filepath, tool_name):
    tools = read_tools_from_config(config_filepath)
    for tool in tools:
        if tool.get("name") == tool_name:
            return tool
    return None


def download_all_logos(config_filepath, logos_dir):
    """
    Attempt to download an SVG logo for all tools in the ecosystem.
    :param config: The ecosystem configuration.
    :param logos_dir: The directory where logos should be saved (should already exist)
    """

    tools = read_tools_from_config(config_filepath)

    for tool_config in tools:
        download_svg(config_filepath=config_filepath, tool_config=tool_config, logos_dir=logos_dir)
