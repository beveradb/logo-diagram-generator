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

    output_svg_path, output_png_path = generate_diagram.generate_diagram_from_config(
        config_filepath=args.config, diagram_name=args.name, output_dir=args.output_dir, logos_dir=args.logos_dir, png_width=args.png_width
    )

    logging.info(f"Logo diagram generator completed successfully! Output filenames: {output_svg_path}, {output_png_path}")


if __name__ == "__main__":
    main()
