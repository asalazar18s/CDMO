FROM minizinc/minizinc:latest

# Install required packages, including python3-venv and correct pip dependencies
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv python3.12-venv

# Set the working directory
WORKDIR /app

# Copy project files
COPY . /app

# Create and activate a virtual environment
RUN python3 -m venv /app/venv && \
    /app/venv/bin/python -m ensurepip --default-pip && \
    /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Set environment variables to use the virtual environment
ENV PATH="/app/venv/bin:$PATH"

CMD ["/bin/bash"]
