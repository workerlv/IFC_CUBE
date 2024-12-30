# --platform added so it works on Macbook M1 silicon (if not working on your machine probably choose different docker image/ platform)
FROM --platform=linux/amd64 python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8515