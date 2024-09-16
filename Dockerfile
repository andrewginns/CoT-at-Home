# Use an official Python runtime as the base image
FROM python:3.11-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy poetry.lock and pyproject.toml to ensure reproducibility
COPY pyproject.toml poetry.lock ./

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy the current directory contents into the container
COPY . .

# Define entrypoint
ENV PORT 5001
# Expose the port your FastAPI app will run on
EXPOSE $PORT
ENTRYPOINT sh -c "python cot.py --port $PORT"