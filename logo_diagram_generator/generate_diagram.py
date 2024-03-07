import os
import re
import logging
import shutil
import xml.dom.minidom
import graphviz
import cairosvg

from logo_diagram_generator import utils


def generate_text_only_svg_diagram_from_config(config, diagram_name, output_svg_path):
    logging.info("Generating text-only SVG diagram from config")

    ecosystem_style = config["ecosystem"].get("style", {})

    diagram_engine = ecosystem_style.get("diagramEngine", "neato")
    diagram_overlap = str(ecosystem_style.get("diagramOverlap", "false"))
    diagram_overlap_scaling = str(ecosystem_style.get("diagramOverlapScaling", "1.0"))
    diagram_overlap_shrink = str(ecosystem_style.get("diagramOverlapShrink", "true"))
    diagram_padding = str(ecosystem_style.get("diagramPadding", "0.5"))
    diagram_rankdir = ecosystem_style.get("diagramRankdir", "TB")

    group_label_shape = ecosystem_style.get("groupLabelShape", "box")
    group_label_style = ecosystem_style.get("groupLabelStyle", "rounded")
    group_label_fontname = ecosystem_style.get("groupLabelFontname", "Helvetica")
    group_label_fontcolor = ecosystem_style.get("groupLabelFontcolor", "#333333")
    group_label_fontsize = str(ecosystem_style.get("groupLabelFontsize", "25"))
    group_label_margin = str(ecosystem_style.get("groupLabelMargin", "0.2"))

    dot = graphviz.Digraph(engine=diagram_engine, format="svg")
    dot.attr(overlap=diagram_overlap)
    dot.attr(overlap_scaling=diagram_overlap_scaling)
    dot.attr(overlap_shrink=diagram_overlap_shrink)
    dot.attr(rankdir=diagram_rankdir)
    dot.attr(pad=diagram_padding)
    dot.attr(id=diagram_name)

    central_tool = config["ecosystem"]["centralTool"]
    central_tool_name = central_tool["name"]
    central_tool_label = central_tool.get("label", central_tool_name)
    logging.debug(f"Central tool: {central_tool_name}")

    central_tool_margin = str(central_tool.get("margin", "0.5"))

    dot.node(
        central_tool_name,
        id=central_tool_name,
        label=central_tool_label,
        shape="ellipse",
        margin=central_tool_margin,
    )

    for i, group in enumerate(config["ecosystem"]["groups"], start=0):
        group_slug = utils.slugify(group["category"])
        group_color = group.get("color", utils.visually_distinct_colors[i % len(utils.visually_distinct_colors)])
        logging.debug(f"Processing group: {group['category']} with color {group_color}")

        group_label = group["category"]
        if len(group_label) > 15:
            group_label = group_label.replace(" ", "\n", 1)

        group_cluster_name = f"cluster_{group_slug}"
        with dot.subgraph(name=group_cluster_name) as c:
            c.attr(id=group_cluster_name)

            # Comment this out to see the cluster boundaries if debugging layout issues
            c.attr(style="invis")

            label_node_name = f"label_{group_slug}"
            c.node(
                label_node_name,
                id=label_node_name,
                label=group_label,
                shape=group_label_shape,
                style=group_label_style,
                fontsize=group_label_fontsize,
                fontname=group_label_fontname,
                fontcolor=group_label_fontcolor,
                margin=group_label_margin,
                color=group_color,
            )

            dot.edge(
                central_tool_name,
                label_node_name,
                arrowsize="0.0",
                color=group_color,
                id=f"{central_tool_name}-{label_node_name}-edge",
            )

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
                c.edge(
                    label_node_name,
                    tool_label,
                    color=group_color,
                    id=f"{label_node_name}-{tool_label}-edge",
                )

    logging.info("Rendering the graph to SVG")
    dot.render(diagram_name, cleanup=True)

    # Move the file from the default diagram name to the specified output path
    shutil.move(f"{diagram_name}.svg", output_svg_path)
    logging.info(f"Diagram moved to {output_svg_path}")


def find_svg_element_by_id(element, id):
    # Check if this element is the one we're looking for
    if element.getAttribute("id") == id:
        return element

    # Recursively search in child elements
    for child in element.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            found = find_svg_element_by_id(child, id)
            if found:
                return found
    return None


def embed_logos_in_diagram(diagram_name, diagram_svg_path, output_svg_path, config, logos_dir):
    logging.info(f"Embedding logos into diagram from {diagram_svg_path}")

    default_logo_scale = config["ecosystem"].get("style", {}).get("defaultLogoScale", 1.5)
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

        logo_scale = tool_config.get("scale", default_logo_scale)
        logo_position_adjust_x = tool_config.get("positionAdjustX", 0)
        logo_position_adjust_y = tool_config.get("positionAdjustY", 0)

        tool_name_slug = utils.slugify(tool_name)
        logo_svg_path = os.path.join(logos_dir, f"{tool_name_slug}.svg")

        # Parse the diagram SVG content to find the node with the right ID for this tool label
        diagram_svg_dom = xml.dom.minidom.parseString(diagram_svg)
        tool_node = find_svg_element_by_id(diagram_svg_dom.documentElement, tool_label)
        diagram_graph_node = find_svg_element_by_id(diagram_svg_dom.documentElement, diagram_name)

        if tool_node is not None:
            logging.info(f"Found node in diagram for tool: {tool_label}, processing and embedding logo SVG")

            ellipse_node = tool_node.getElementsByTagName("ellipse")[0]
            cx = ellipse_node.getAttribute("cx")
            cy = ellipse_node.getAttribute("cy")
            logging.debug(f"Found ellipse with cx: {cx} and cy: {cy}")

            logging.debug(f"Parsing logo SVG content to add transform and embed")
            with open(logo_svg_path, "r") as file:
                logo_svg_content = file.read()

            logging.debug(f"Performing find/replace to add {tool_name_slug}- prefix to generic classes, IDs, and hrefs")
            class_search_1 = re.search(r'class="st\d+"', logo_svg_content)
            if class_search_1:
                logging.debug(f"Adding {tool_name_slug}- prefix to generic class {class_search_1.group()}")
                logo_svg_content = re.sub(r"(st\d+)", f"{tool_name_slug}-\\1", logo_svg_content)

            class_search_2 = re.search(r'class="cls-\d+"', logo_svg_content)
            if class_search_2:
                logging.debug(f"Adding {tool_name_slug}- prefix to generic class {class_search_2.group()}")
                logo_svg_content = re.sub(r"(cls-\d+)", f"{tool_name_slug}-\\1", logo_svg_content)

            id_search = re.findall(r'id="([^"]+)"', logo_svg_content)
            href_search = re.findall(r'xlink:href="#([^"]+)"', logo_svg_content)

            for id_match in id_search:
                logging.debug(f"Adding {tool_name_slug}- prefix to ID {id_match}")
                logo_svg_content = re.sub(f'id="{id_match}"', f'id="{tool_name_slug}-{id_match}"', logo_svg_content)

            for href_match in href_search:
                logging.debug(f"Adding {tool_name_slug}- prefix to href #{href_match}")
                logo_svg_content = re.sub(f'xlink:href="#{href_match}"', f'xlink:href="#{tool_name_slug}-{href_match}"', logo_svg_content)

            css_url_search = re.findall(r"url\(#([^)]+)\)", logo_svg_content)
            for css_url_match in css_url_search:
                logging.debug(f"Adding {tool_name_slug}- prefix to CSS URL reference #{css_url_match}")
                logo_svg_content = re.sub(f"url\(#{css_url_match}\)", f"url(#{tool_name_slug}-{css_url_match})", logo_svg_content)

            logo_svg_dom = xml.dom.minidom.parseString(logo_svg_content)
            logo_node = logo_svg_dom.documentElement

            logo_orig_width = 120
            logo_orig_height = 60

            logo_scaled_width = logo_orig_width * logo_scale
            logo_scaled_height = logo_orig_height * logo_scale

            transform_x = float(cx) - (logo_scaled_width / 2) + logo_position_adjust_x
            transform_y = float(cy) - (logo_scaled_height / 2) + logo_position_adjust_y
            logging.debug(f"Translating logo to the position ({transform_x}, {transform_y})")
            transform_attr = f"translate({transform_x}, {transform_y}) scale({logo_scale})"

            logo_node_id = f"{tool_name_slug}-logo"
            logo_node.setAttribute("id", logo_node_id)
            logo_node.setAttribute("transform", transform_attr)
            logo_node.setAttribute("width", str(logo_orig_width))
            logo_node.setAttribute("height", str(logo_orig_height))

            # Remove the tool node completely and insert the logo node at the end of the diagram documentElement
            tool_node.parentNode.removeChild(tool_node)
            diagram_graph_node.appendChild(logo_node)

            # Update the diagram SVG with the modified DOM
            diagram_svg = diagram_svg_dom.toxml()
        else:
            logging.warning(f"No node found in diagram for tool: {tool_name}")

    with open(output_svg_path, "w") as file:
        file.write(diagram_svg)

    logging.info("Logos embedded into diagram")


def generate_diagram_from_config(config_filepath, diagram_name, output_dir, logos_dir, png_width):
    logging.info(f"Reading configuration from file: {config_filepath}")
    config = utils.read_config(config_filepath)

    text_diagram_basename = utils.slugify(diagram_name)
    logging.info(f"Filesystem safe diagram name: {text_diagram_basename}")

    logging.info(f"Logos directory: {logos_dir}")
    logging.info(f"Output directory: {output_dir}")

    text_diagram_svg_path = os.path.join(output_dir, f"{text_diagram_basename}_text.svg")
    logging.info(f"Text only diagram SVG output path: {text_diagram_svg_path}")

    # Determining the output path for the SVG diagram with logos
    output_svg_path = os.path.join(output_dir, f"{text_diagram_basename}_logos.svg")
    logging.info(f"Logos diagram SVG output path: {output_svg_path}")

    # Generating the text-only SVG diagram based on the configuration
    generate_text_only_svg_diagram_from_config(config, diagram_name=text_diagram_basename, output_svg_path=text_diagram_svg_path)
    logging.info("Generated text-only SVG diagram from configuration.")

    # Embedding logos into the text-only SVG diagram
    embed_logos_in_diagram(
        diagram_name=text_diagram_basename,
        diagram_svg_path=text_diagram_svg_path,
        output_svg_path=output_svg_path,
        config=config,
        logos_dir=logos_dir,
    )

    # Convert SVG content to PNG
    png_output_path = output_svg_path.replace(".svg", ".png")
    cairosvg.svg2png(url=output_svg_path, write_to=png_output_path, output_width=png_width)
    logging.info(f"PNG version of the diagram saved to {png_output_path}, with width set to {png_width} pixels")

    logging.info(f"Final diagram with embedded logos generated")

    return output_svg_path, png_output_path
