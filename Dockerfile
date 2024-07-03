# --- Build Stage ---
FROM python:3.11 as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_VERSION=1.7.1

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Set the working directory in the builder stage
WORKDIR /app

# Copy the pyproject.toml and poetry.lock files
COPY pyproject.toml poetry.lock* /app/

# Debugging step: Print the current directory and list files
RUN echo "Current directory: $(pwd)" && ls -la

# Install runtime dependencies using Poetry and create wheels for them
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction --no-ansi \
    && poetry export -f requirements.txt --output requirements.txt --without-hashes \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /tmp/wheels -r requirements.txt

# Copy the rest of your application's code
COPY annatar /app/annatar

# Build your application using Poetry
RUN poetry build

# --- Final Stage ---
FROM python:3.11-slim as final

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/annatar.db
ENV NUM_WORKERS=4
ENV CONFIG_FILE=/config/annatar.yaml

# Create volume and set working directory
VOLUME /app/data
WORKDIR /app

# Copy wheels and built wheel from the builder stage
COPY --from=builder /tmp/wheels /tmp/wheels/
COPY --from=builder /app/dist/*.whl /tmp/wheels/

# Install the application package along with all dependencies
RUN pip install /tmp/wheels/*.whl && rm -rf /tmp/wheels

# Copy static and template files
COPY ./static /app/static
COPY ./templates /app/templates
COPY run.py /app/run.py

# Add entrypoint script and set it as the command
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Define the default command
CMD ["sh", "/app/entrypoint.sh"]
