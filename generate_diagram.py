import yaml
import graphviz
import os
import re
import xml
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
from svgpathtools import svg2paths, wsvg
from svgpathtools.paths2svg import big_bounding_box
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def read_config(config_path):
    logging.debug(f"Reading configuration from {config_path}")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


# Function to sanitize tool names, labels, and aliases for URL
def sanitize_for_url(text):
    logging.debug(f"Sanitizing text for URL: {text}")
    sanitized_text = "".join(
        char.lower() if char.isalnum() or char == " " or char == "_" else ""
        for char in text
    ).replace(" ", "_")
    logging.debug(f"Sanitized text: {sanitized_text}")
    return sanitized_text


def generate_text_only_svg_diagram_from_config(config, diagram_name):
    logging.info("Generating text-only SVG diagram from config")
    distinct_colors = [
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

    dot = graphviz.Digraph(engine="neato", format="svg")
    dot.attr(overlap="false")
    dot.attr(rankdir="TB")
    dot.attr(pad="1")

    central_tool = config["ecosystem"]["centralTool"]["name"]
    logging.debug(f"Central tool: {central_tool}")

    dot.node(
        central_tool,
        id=central_tool,
        label=central_tool,
        shape="ellipse",
        margin="0.5",
    )

    for i, group in enumerate(config["ecosystem"]["groups"], start=0):
        group_slug = sanitize_for_url(group["category"])
        group_color = distinct_colors[i % len(distinct_colors)]
        logging.debug(f"Processing group: {group['category']} with color {group_color}")

        group_label = group["category"]
        if len(group_label) > 15:
            group_label = group_label.replace(" ", "\n", 1)

        with dot.subgraph(name=f"cluster_{group_slug}") as c:
            c.attr(style="invis")

            label_node_name = f"label_{group_slug}"
            c.node(
                label_node_name,
                id=label_node_name,
                label=group_label,
                shape="box",
                fontsize="20",
                color=group_color,
            )

            dot.edge(central_tool, label_node_name, arrowsize="0.0")

            for tool in group["tools"]:
                tool_label = tool.get("label", tool["name"])
                c.node(
                    tool_label,
                    id=tool_label,
                    label=tool_label,
                    shape="ellipse",
                    margin="0.3",
                    color=group_color,
                )
                c.edge(label_node_name, tool_label, color=group_color)

    logging.info("Rendering the graph to SVG")
    dot.render(diagram_name, cleanup=True)


def scale_svg_to_width(svg_input_path, svg_output_path, target_width):
    logging.debug(f"Scaling SVG from {svg_input_path} to width {target_width}")
    try:
        paths, attributes = svg2paths(svg_input_path)

        if not paths:
            logging.warning(f"No paths found in SVG: {svg_input_path}.")

        logging.debug(f"Number of paths found: {len(paths)}")

        valid_paths = []  # List to hold paths with valid bounding boxes
        for i, path in enumerate(paths):
            logging.debug(f"Processing path {i + 1} of {len(paths)}")
            try:
                path.bbox()  # Attempt to calculate bounding box
                valid_paths.append(path)  # Add to valid_paths if successful
            except Exception as e:
                logging.error(f"Error calculating bounding box for a path: {e}")
                continue  # Skip paths that cause errors

        if not valid_paths:
            logging.error("No valid bounding boxes found for any paths.")
            return

        min_x, max_x, min_y, max_y = big_bounding_box(
            valid_paths
        )  # Use valid_paths here
        current_width = max_x - min_x
        scale_factor = target_width / current_width
        scaled_paths = [
            path.scaled(scale_factor) for path in valid_paths
        ]  # Scale valid paths

        wsvg(scaled_paths, attributes=attributes, filename=svg_output_path)
        logging.info(f"SVG scaled and saved to {svg_output_path}")
    except Exception as e:
        logging.error(f"Error scaling SVG: {e}")
        raise


def find_element_by_id(element, id):
    # Check if this element is the one we're looking for
    if element.getAttribute("id") == id:
        return element

    # Recursively search in child elements
    for child in element.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            found = find_element_by_id(child, id)
            if found:
                return found
    return None


def embed_logos_in_diagram(diagram_svg_path, output_svg_path, config, logos_dir):
    logging.info(f"Embedding logos into diagram from {diagram_svg_path}")
    with open(diagram_svg_path, "r") as file:
        diagram_svg = file.read()

    tools = []
    central_tool = config["ecosystem"].get("centralTool", {})
    if central_tool.get("name"):
        tools.append(central_tool)

    for group in config["ecosystem"].get("groups", []):
        for tool in group.get("tools", []):
            tools.append(tool)

    for tool_config in tools:
        tool_name = tool_config.get("name")
        tool_label = tool_config.get("label", tool_name)
        tool_name_slug = sanitize_for_url(tool_name)
        logo_svg_path = os.path.join(logos_dir, f"{tool_name_slug}.svg")

        # Parse the diagram SVG content to find the node with the right ID for this tool label
        diagram_svg_dom = xml.dom.minidom.parseString(diagram_svg)
        tool_node = find_element_by_id(diagram_svg_dom.documentElement, tool_label)

        if tool_node is not None:
            logging.debug(f"Found node in diagram for tool: {tool_label}")

            ellipse_node = tool_node.getElementsByTagName("ellipse")[0]
            cx = ellipse_node.getAttribute("cx")
            cy = ellipse_node.getAttribute("cy")
            logging.debug(f"Found ellipse with cx: {cx} and cy: {cy}")

            # Parse the logo SVG content to be inserted
            logging.debug(f"Parsing logo SVG content to add transform and embed")
            with open(logo_svg_path, "r") as file:
                logo_svg_content = file.read()

            logo_svg_dom = xml.dom.minidom.parseString(logo_svg_content)
            logo_node = logo_svg_dom.documentElement

            # Translate the logo node to the position (cx, cy)
            transform_attr = f"translate({cx}, {cy})"
            logo_node.setAttribute("transform", transform_attr)

            # Replace the tool node with the logo node
            tool_node.parentNode.replaceChild(logo_node, tool_node)

            # Update the diagram SVG with the modified DOM
            diagram_svg = diagram_svg_dom.toxml()
        else:
            logging.warning(f"No node found in diagram for tool: {tool_name}")

    with open(output_svg_path, "w") as file:
        file.write(diagram_svg)

    logging.info("Logos embedded into diagram")


config = read_config("config.yml")
generate_text_only_svg_diagram_from_config(config, diagram_name="text_diagram")

# Embed logos directly into the diagram SVG
embed_logos_in_diagram(
    diagram_svg_path="text_diagram.svg",
    output_svg_path="logo_diagram.svg",
    config=config,
    logos_dir="logos",
)
