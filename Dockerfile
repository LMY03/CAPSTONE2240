FROM python:3

ENV PYTHONUNBUFFERED 1

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -r requirements.txt

COPY . /code/

# # Use the official Python image from the Docker Hub
# FROM python:3.9-slim

# # Set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # Install dependencies
# RUN apt-get update \
#     && apt-get install -y gcc libpq-dev musl-dev libmariadb-dev pkg-config

# # Set working directory
# WORKDIR /app

# # Install Python dependencies
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the entrypoint script
# COPY entrypoint.sh /entrypoint.sh
# RUN chmod +x /entrypoint.sh

# # Copy the rest of the application code
# COPY . /app/

# # Entrypoint
# ENTRYPOINT ["/entrypoint.sh"]
