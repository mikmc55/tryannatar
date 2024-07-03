#!/bin/sh

# Set up Prometheus multiproc directory
export PROMETHEUS_MULTIPROC_DIR="${PROMETHEUS_MULTIPROC_DIR:-/tmp/prometheus/metrics}"
echo "Using Prometheus multiproc directory: $PROMETHEUS_MULTIPROC_DIR"

# Remove and recreate directory
if [ -d "$PROMETHEUS_MULTIPROC_DIR" ]; then
    echo "Removing existing Prometheus multiproc directory..."
    rm -rf "$PROMETHEUS_MULTIPROC_DIR"
fi
echo "Creating Prometheus multiproc directory..."
mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

# Start the application
echo "Starting the application..."
exec python run.py
