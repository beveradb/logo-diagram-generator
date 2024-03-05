# Ecosystem Diagram Generator

This tool allows you to generate SVG diagrams that visually represent an ecosystem of tools, complete with their logos, based on a YAML configuration file. It's particularly useful for visualizing the relationships and categories of various tools within a technology stack.

## Example Output

Below is an example of what the generated diagram looks like, generated with the example config: `python generate_diagram.py -c config.yml.example`

![Example Diagram](examples/example_logos.svg)

## Quick Start

1. **Clone the repository**

   Start by cloning this repository to your local machine.

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install Dependencies**

   Ensure you have Python installed on your system. Then, install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Your Configuration**

   Create a `config.yml` file based on the provided `config.yml.example`. This file should list all the tools in your ecosystem, categorized appropriately. For example:

   ```yaml
   ecosystem:
     centralTool:
       name: Kubernetes
     groups:
       - category: Cluster Management
         tools:
           - name: Rancher
   ```

   If you know a particular tool has a different alias on VectorLogoZone (e.g. `helmsh` instead of just `helm`), set the `alias` value in the config.

   If you know you want a logo to be downloaded from a specific URL, set the `svgURL` value in the config.

   See `config.yml.example` for example configurations!

4. **Download Logos**

   Run the `download_logos.py` script to automatically download SVG logos for the tools listed in your `config.yml`. The script attempts to fetch logos based on the tool's name, label, or alias, by default into a directory called `logos`.

   ```bash
   python download_logos.py
   ```

   The config file path and logos directory path can be customised, add `--help` for available CLI params.

5. **Generate Diagram**

   With the logos downloaded, you can now generate the ecosystem diagram by running the `generate_diagram.py` script.

   ```bash
   python generate_diagram.py
   ```

   This will produce an SVG file named `diagram_logos.svg` in your current directory.

   The config file path, logos directory path and diagram name can be customised, add `--help` for available CLI params.

## Customizing Your Diagram

- **Configuration File**: Modify `config.yml` to add, remove, or categorize tools as needed. Each tool can have a `name`, `label`, and optionally an `alias` or `svgURL` for custom logo URLs.
- **Logo Download**: If the automatic logo download doesn't find a logo for a tool, you can manually place an SVG file in the `logos` directory. The file name should match the tool's name in the configuration file.
- **Diagram Appearance**: Modify the `generate_diagram.py` script if you need to change the size, layout, or appearance of the generated diagram.

## Troubleshooting

- **Missing Logos**: Ensure all tools in your `config.yml` have either a valid `svgURL` or a corresponding SVG file in the `logos` directory.
- **Script Errors**: Check the Python script logs for any error messages. Most issues can be resolved by ensuring the configuration file is correctly formatted and all dependencies are installed.

## Contributing

Contributions to improve the tool or add new features are welcome. Please submit a pull request or open an issue to discuss your ideas.
