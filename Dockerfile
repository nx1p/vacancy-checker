FROM python:3.11.9-alpine3.20

# Install poetry
RUN pip install poetry==1.5.1

# Set environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    DATA_DIR=/app

WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* ./

# Install project (and dependencies)
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Copy only the necessary files
COPY vacancy_checker.py ./

# Create data directory
RUN mkdir -p /app/data

# Run the application
CMD ["poetry", "run", "python", "vacancy_checker.py"]
