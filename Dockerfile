# Utiliser l'image Python officielle comme base
FROM python:3.12

# Installer Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Ajouter Poetry au PATH
ENV PATH="/root/.local/bin:$PATH"

# Copier les fichiers de votre projet dans le conteneur
WORKDIR /app
COPY . /app

# Installer les dépendances avec Poetry
RUN poetry install --no-root --no-dev

# Exécuter le script Python
CMD ["poetry", "run", "python", "/app/kuma_ingress_watcher/controller.py"]
