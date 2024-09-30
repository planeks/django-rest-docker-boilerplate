# Use the official Python image
FROM python:3.12-bullseye

# Set environment variables at the beginning
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.8.2  \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/code" \
    VENV_PATH="/code/.venv"
# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
# Install dependencies
RUN apt-get update \
    && apt-get install -y build-essential libpq-dev gettext curl graphviz \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN curl -sSL https://install.python-poetry.org | python3 -

# Create appuser
RUN addgroup --gid 1024 appuser \
    && adduser --disabled-password --gecos "" --force-badname --ingroup appuser appuser

# Copy only pyproject.toml and poetry.lock first (for better caching)
COPY --chown=appuser:appuser ./src/pyproject.toml ./src/poetry.lock /opt/project/src/

# Accept build argument to determine environment
ARG ENVIRONMENT=production

# Install dependencies
WORKDIR /opt/project/src
RUN if [ "$ENVIRONMENT" = "production" ] ; then \
        poetry install --no-root --only main; \
    else \
        poetry install --no-root; \
    fi

# Copy entrypoint
COPY --chown=appuser:appuser ./docker/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

# We use the directory /opt/project/src for PyCharm compatibility
COPY --chown=appuser:appuser ./src /opt/project/src

RUN mkdir /data
RUN chown -R appuser:appuser /data
RUN chmod 775 /data
RUN chmod g+s /data

# Switch to non-root user
USER appuser

WORKDIR /opt/project/src

ENTRYPOINT ["/entrypoint"]
