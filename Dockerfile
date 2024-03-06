FROM python:3.12-slim

# Install graphviz
RUN apt-get update && apt-get install -y graphviz && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install the logo-diagram-generator package
RUN pip install logo-diagram-generator

# Configure docker to run the logo-diagram-generator
ENTRYPOINT ["logo-diagram-generator"]

# Set the default args to pass if none are specified
CMD [ "--help" ]
