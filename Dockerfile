# Use a base Python image
FROM python:3.9.6

# Set the working directory inside the container
WORKDIR /cdmo

# Copy the project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Keep the container running (optional)
CMD ["tail", "-f", "/dev/null"]
