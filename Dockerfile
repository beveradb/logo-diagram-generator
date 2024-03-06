FROM python:3.12-slim

# Install graphviz
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install the logo-diagram-generator package
RUN pip install logo-diagram-generator

# Set the default command to run the logo-diagram-generator
CMD ["logo-diagram-generator"]
