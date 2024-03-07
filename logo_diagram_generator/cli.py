import os
import argparse
import logging

from logo_diagram_generator import download_logos, generate_diagram, utils


def main():
    parser = argparse.ArgumentParser(
        description="Generate SVG diagrams of a tech ecosystem, using logos from each tool organised into groups around a central logo.",
        formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=80),
    )
    parser.add_argument("-d", "--debug", action="store_true", help="enable debug logging, equivalent to --log_level=debug")
    parser.add_argument("--log_level", default="info", help="log level, e.g. info, debug, warning (default: %(default)s)")

    parser.add_argument("-n", "--name", default="diagram", help="Base name for the output SVG files.")
    parser.add_argument("-c", "--config", default="config.yml", help="Path to the configuration file.")
    parser.add_argument("-l", "--logos_dir", default="logos", help="Directory where logos are stored.")
    parser.add_argument("-s", "--skip_download", default=False, help="Skip downloading logos before generating.")
    parser.add_argument(
        "-o",
        "--output_dir",
        default=os.getcwd(),
        help="Directory for the output SVG diagram.",
    )
    parser.add_argument("-w", "--png_width", type=int, default=3000, help="Width of the resulting PNG image (default: 3000).")
    parser.add_argument(
        "-oc",
        "--override",
        type=lambda kv: dict([kv.split("=")]),
        action="append",
        help="Override specific configuration entries. Use format: key=value. This option can be used multiple times for multiple overrides.",
    )
    parser.add_argument(
        "-t",
        "--theme",
        choices=["dark", "light"],
        default=None,
        help="Theme for the diagram, either 'dark' or 'light' (default: %(default)s)",
    )

    args = parser.parse_args()

    if args.debug:
        log_level = logging.DEBUG
    else:
        log_level = getattr(logging, args.log_level.upper())

    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(module)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=log_level
    )

    logging.info(f"Checking logos directory exists: {args.logos_dir}")
    utils.ensure_directory_exists(args.logos_dir)

    if not args.skip_download:
        logging.info(f"Downloading all logos to directory: {args.logos_dir}")
        download_logos.download_all_logos(config_filepath=args.config, logos_dir=args.logos_dir)
        logging.info(f"Downloaded all logos to directory: {args.logos_dir}")

    # args.override is e.g. [{'style.diagramBackgroundColor': '#111111'}]
    theme_overrides = None
    if args.theme == "dark":
        theme_overrides = {
            "style.groupLabelFontcolor": "#ffffff",
            "style.colorPalette": "aqua,purple3,maroon3,orangered,yellow,lime,fuchsia,cornflower,peachpuff,forestgreen",
            "style.defaultLogoStrokeColor": "white",
            "style.defaultLogoStrokeWidth": "0.5",
        }
    elif args.theme == "light":
        theme_overrides = {
            "style.groupLabelFontcolor": "#222222",
            "style.colorPalette": "seagreen,maroon,midnightblue,olive,red,mediumblue,darksalmon,darkgreen,orange",
            "style.defaultLogoStrokeColor": "#333333",
            "style.defaultLogoStrokeWidth": "0.2",
        }

    if theme_overrides is not None:
        overrides = args.override if args.override is not None else []
        # Merge all dictionaries in the list into a single dictionary
        combined_overrides = {k: v for d in overrides for k, v in d.items()}
        combined_overrides.update(theme_overrides)
        args.override = [combined_overrides]

    output_svg_path, output_png_path = generate_diagram.generate_diagram_from_config(
        config_filepath=args.config,
        diagram_name=args.name,
        output_dir=args.output_dir,
        logos_dir=args.logos_dir,
        png_width=args.png_width,
        override_configs=args.override,
    )

    logging.info(f"Logo diagram generator completed successfully! Output filenames: {output_svg_path}, {output_png_path}")


if __name__ == "__main__":
    main()
