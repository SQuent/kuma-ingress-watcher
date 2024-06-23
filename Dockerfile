FROM python:3.12-slim as base

RUN apt-get update && apt-get install -y gcc libffi-dev g++

# Copier les fichiers de votre projet dans le conteneur
WORKDIR /app
COPY . /app

# Installer Poetry
RUN curl -sSL https://install.python-poetry.org| python -

# Activer l'utilisation de Poetry dans le shell
ENV PATH="${PATH}:$HOME/.local/bin"

# Installer les dépendances avec Poetry
RUN ~/.local/share/pypoetry/venv/bin/poetry install --no-root --no-dev

# Exécuter le script Python
CMD ["python", "/app/controller.py"]
