FROM python:3.12-slim

# Install graphviz
RUN apt-get update && apt-get install -y graphviz wget && rm -rf /var/lib/apt/lists/*

# Install fonts
COPY fonts /usr/share/fonts/truetype/custom
RUN fc-cache -fv

# Set the working directory
WORKDIR /app

# Install package globally with pip
COPY . /app
RUN pip install .

# Configure docker to run the logo-diagram-generator command
ENTRYPOINT ["logo-diagram-generator"]

# Set the default args to pass if none are specified
CMD [ "--help" ]
