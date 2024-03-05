import os
import argparse
import logging

from logo_diagram_generator import download_logos, generate_diagram, utils


def main():
    parser = argparse.ArgumentParser(
        description="Generate SVG diagrams of a tech ecosystem, using logos from each tool organised into groups around a central logo."
    )
    parser.add_argument("-n", "--name", default="diagram", help="Base name for the output SVG files.")
    parser.add_argument("-c", "--config", default="config.yml", help="Path to the configuration file.")
    parser.add_argument("-l", "--logos_dir", default="logos", help="Directory where logos are stored.")
    parser.add_argument("-d", "--skip_download", default=False, help="Skip downloading logos before generating.")
    parser.add_argument(
        "-o",
        "--output_dir",
        default=os.getcwd(),
        help="Directory for the output SVG diagram.",
    )

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

    args = parser.parse_args()

    logging.info(f"Checking logos directory exists: {args.logos_dir}")
    utils.ensure_directory_exists(args.logos_dir)

    if not args.skip_download:
        logging.info(f"Downloading all logos to directory: {args.logos_dir}")
        download_logos.download_all_logos(config_filepath=args.config, logos_dir=args.logos_dir)
        logging.info(f"Downloaded all logos to directory: {args.logos_dir}")

    output_svg_path = generate_diagram.generate_diagram_from_config(
        config_filepath=args.config, diagram_name=args.name, output_dir=args.output_dir, logos_dir=args.logos_dir
    )

    logging.info(f"Logo diagram generator completed successfully! Output filename: {output_svg_path}")


if __name__ == "__main__":
    main()
