FROM python:3.12-slim

# Install graphviz
RUN apt-get update && apt-get install -y graphviz wget && rm -rf /var/lib/apt/lists/*

# Install fonts
RUN mkdir /usr/share/fonts/truetype/Avenir-Next && \
    wget -qO- https://raw.githubusercontent.com/prchann/fonts/main/Avenir%20Next/400%20Regular/avenir-next-regular.ttf > /usr/share/fonts/truetype/Avenir-Next/Avenir-Next.ttf && \
    fc-cache -fv

# Set the working directory
WORKDIR /app

# Install the logo-diagram-generator package
RUN pip install logo-diagram-generator

# Configure docker to run the logo-diagram-generator
ENTRYPOINT ["logo-diagram-generator"]

# Set the default args to pass if none are specified
CMD [ "--help" ]
