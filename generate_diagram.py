import yaml
import graphviz
import os
import re
import xml.etree.ElementTree as ET
from svgpathtools import svg2paths, wsvg
from svgpathtools.paths2svg import big_bounding_box


def read_config(config_path):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


# Function to sanitize tool names, labels, and aliases for URL
def sanitize_for_url(text):
    return "".join(
        char.lower() if char.isalnum() or char == " " or char == "_" else ""
        for char in text
    ).replace(" ", "_")


def generate_diagram_from_config(config):
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
    dot.attr(overlap="ipsep", mode="ipsep")
    dot.attr(rankdir="TB")  # Encourage a top-to-bottom layout
    dot.attr(ranksep="1.0")  # Increase distance between ranks

    central_tool = config["ecosystem"]["centralTool"]["name"]

    # Add the central tool node
    dot.node(central_tool, label=central_tool, shape="ellipse")

    # Create a subgraph for each group
    for i, group in enumerate(config["ecosystem"]["groups"], start=0):
        group_slug = sanitize_for_url(group["category"])
        group_color = distinct_colors[i % len(distinct_colors)]

        # Wrap group names onto two lines if necessary
        group_label = group["category"]
        if len(group_label) > 15:  # Arbitrary length for when to wrap text
            group_label = group_label.replace(
                " ", "\n", 1
            )  # Replace the first space with a newline

        with dot.subgraph(name=f"cluster_{group_slug}") as c:
            c.attr(color=group_color)
            c.attr(style="rounded")

            # Add an anchor node for the group
            group_anchor_name = f"anchor_{group_slug}"
            c.node(group_anchor_name, shape="point", width="0.1")

            for tool in group["tools"]:
                tool_label = tool.get("label", tool["name"])
                # Add each tool node within the subgraph
                c.node(tool_label, label=tool_label, shape="ellipse")
                c.edge(group_anchor_name, tool_label)

            # Add an edge from the central tool to the anchor node of the group
            dot.edge(central_tool, group_anchor_name)

    # Render the graph to SVG
    dot.render("diagram", cleanup=True)


def scale_svg_to_width(svg_input_path, svg_output_path, target_width):
    # Load the paths and attributes from the SVG
    paths, attributes = svg2paths(svg_input_path)

    # Calculate the current bounding box of all paths
    min_x, max_x, min_y, max_y = big_bounding_box(paths)
    current_width = max_x - min_x

    # Calculate the scale factor
    scale_factor = target_width / current_width

    # Scale all paths
    scaled_paths = [path.scaled(scale_factor) for path in paths]

    # Write the scaled paths back to a new SVG file
    wsvg(scaled_paths, attributes=attributes, filename=svg_output_path)


def prepare_svg_for_embedding(svg_path):
    with open(svg_path, "r") as file:
        svg_content = file.read()
    # Remove XML declaration and DOCTYPE
    svg_content = re.sub(
        r"<\?xml .*\?>|<!DOCTYPE .*>\n", "", svg_content, flags=re.MULTILINE
    )
    # Extract the attributes from the <svg> tag
    svg_tag_match = re.search(r"<svg([^>]*)>", svg_content, flags=re.MULTILINE)
    svg_attributes = svg_tag_match.group(1) if svg_tag_match else ""
    # Remove outer <svg> tag, preserving the attributes and inner content
    svg_content = re.sub(r"<svg[^>]*>(.*)</svg>", r"\1", svg_content, flags=re.DOTALL)
    # Return the attributes along with the inner SVG content
    return svg_attributes, svg_content.strip()


def set_svg_dimensions_and_viewBox(svg_path, output_path, width, height, viewBox):
    # Parse the SVG file
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Set the width and height attributes
    root.attrib["width"] = width
    root.attrib["height"] = height

    # Set the viewBox attribute
    root.attrib["viewBox"] = viewBox

    # Write the modified SVG to a new file
    tree.write(output_path)


def remove_transform_property(svg_path, output_path):
    # Parse the SVG file
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Find the <g> element with the specific id 'graph0'
    # Note: The namespace (ns0) handling might vary depending on the SVG. Adjust as necessary.
    # If your SVG uses namespaces, you might need to find the correct namespace URI and use it.
    namespaces = {
        "ns": "http://www.w3.org/2000/svg"
    }  # Adjust the namespace URI as necessary
    graph_element = root.find(".//ns:g[@id='graph0']", namespaces=namespaces)

    if graph_element is not None:
        # Check if the 'transform' attribute exists and delete it
        if "transform" in graph_element.attrib:
            del graph_element.attrib["transform"]

    # Write the modified SVG to a new file
    tree.write(output_path)


def embed_logos_in_diagram(diagram_svg_path, logos):
    with open(diagram_svg_path, "r") as file:
        diagram_svg = file.read()

    for label, logo_svg_filename in logos.items():
        logo_svg_path = os.path.join(
            os.path.join(os.getcwd(), "logos"), logo_svg_filename
        )
        scaled_logo_svg_path = os.path.join(
            os.path.join(os.getcwd(), "resized_logos_svg"), logo_svg_filename
        )
        scale_svg_to_width(logo_svg_path, scaled_logo_svg_path, target_width=100.0)

        svg_attributes, logo_svg_content = prepare_svg_for_embedding(logo_svg_path)
        # Construct a regex pattern to find the <text> tag for the placeholder
        pattern = re.compile(
            r"(<text[^>]*>.*?" + re.escape(label) + r".*?</text>)", re.DOTALL
        )
        # Insert the SVG content with attributes after the <text> tag
        replacement = r"\1<g " + svg_attributes + ">" + logo_svg_content + "</g>"
        diagram_svg = re.sub(pattern, replacement, diagram_svg)

    with open(diagram_svg_path, "w") as file:
        file.write(diagram_svg)

    # Set the root SVG width, height, and viewBox after embedding logos
    set_svg_dimensions_and_viewBox(
        diagram_svg_path,
        diagram_svg_path,
        "1000pt",
        "1000pt",
        "-100.00 -800.00 1000 1000",
    )

    # Remove the transform property from the specified <g> tag
    remove_transform_property(diagram_svg_path, diagram_svg_path)


config = read_config("config.yml")
generate_diagram_from_config(config)

# Embed logos directly into the diagram SVG
# embed_logos_in_diagram("diagram.svg")
