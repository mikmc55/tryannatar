#!/bin/sh

# Set up the Prometheus multiproc directory
export PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus/metrics}"
echo "Using Prometheus multiproc directory: $PROMETHEUS_MULTIPROC_DIR"

# Remove any existing Prometheus multiproc directory and recreate it
if [ -d "$PROMETHEUS_MULTIPROC_DIR" ]; then
    echo "Removing existing Prometheus multiproc directory..."
    rm -rf "$PROMETHEUS_MULTIPROC_DIR"
fi

echo "Creating Prometheus multiproc directory..."
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

# Run the Python application
echo "Starting the Python application..."
exec python /app/run.py
