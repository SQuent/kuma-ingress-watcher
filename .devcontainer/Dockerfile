FROM mcr.microsoft.com/devcontainers/python:3.12

# Set environment variables
ENV POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
ENV PATH="${POETRY_HOME}/bin:${PATH}"

# Set working directory
WORKDIR /app                        

# Copy only dependency files for cache
COPY pyproject.toml ./

# Install dependencies without development dependencies
RUN poetry install --no-root --only main