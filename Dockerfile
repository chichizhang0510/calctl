# ============================================================================
# Multi-stage build for minimal image size
# ============================================================================

# Build stage: Install dependencies and build the package
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (for caching)
COPY pyproject.toml ./
COPY src/ ./src/

# Build the wheel
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ============================================================================
# Runtime stage: Minimal image with non-root user
# ============================================================================

FROM python:3.10-slim

# Create non-root user
RUN groupadd -r calctl && \
    useradd -r -g calctl -u 1000 -m -s /bin/bash calctl

# Set working directory
WORKDIR /app

# Install runtime dependencies only
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels

# Create data directory with proper permissions
RUN mkdir -p /data && \
    chown -R calctl:calctl /data && \
    mkdir -p /home/calctl/.calctl && \
    chown -R calctl:calctl /home/calctl/.calctl

# Switch to non-root user
USER calctl

# Set environment variables
ENV CALCTL_DATA_DIR=/home/calctl/.calctl \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Define volume for persistent data
VOLUME ["/home/calctl/.calctl"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD calctl --version || exit 1

# Default command
ENTRYPOINT ["calctl"]
CMD ["--help"]

# Metadata
LABEL org.opencontainers.image.title="calctl" \
      org.opencontainers.image.description="A command-line calendar manager" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.authors="Your Name" \
      org.opencontainers.image.source="https://github.com/yourusername/calctl"