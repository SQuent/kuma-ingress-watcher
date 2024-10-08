# Étape 1: Construire les dépendances dans une image intermédiaire
FROM python:3.13 AS builder

# Installer Poetry
RUN curl -sSL https://install.python-poetry.org | python -

# Ajouter Poetry au PATH
ENV PATH="/root/.local/bin:$PATH"

# Définir le répertoire de travail
WORKDIR /app

# Copier uniquement les fichiers de dépendance pour le cache
COPY pyproject.toml ./

# Installer les dépendances sans les dépendances de développement
RUN poetry install --no-root --only main

# Étape 2: Construire l'image finale
FROM python:3.13-slim

# Copier les dépendances installées depuis l'image builder
COPY --from=builder /root/.local /root/.local 
COPY --from=builder /root/.cache/pypoetry/virtualenvs /root/.cache/pypoetry/virtualenvs

# Ajouter Poetry au PATH
ENV PATH="/root/.local/bin:$PATH"

# Définir le répertoire de travail
WORKDIR /app

# Copier le reste des fichiers de l'application
COPY . /app

# Exécuter le script Python
CMD ["poetry", "run", "python", "/app/kuma_ingress_watcher/controller.py"]
