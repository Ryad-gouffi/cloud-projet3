Projet 3 - API MinIO

Microservice REST pour gestion de fichiers avec métadonnées.
  Technologies

    FastAPI (Python)

    MinIO (stockage S3)

    PostgreSQL

    Docker Compose

  Fonctionnalités

    Upload fichiers → MinIO

    Download fichiers

    Suppression fichiers

    Métadonnées (taille, hash SHA256, type, date)

    Stockage métadonnées PostgreSQL

  Démarrage rapide
bash

git clone [repo-url]
cd project-3
docker-compose up -d

API: http://localhost:8000
MinIO: http://localhost:9000 (admin/admin123)
📁 Endpoints Principaux

    POST /upload/ - Upload fichier

    GET /download/{id} - Télécharger

    GET /files/{id}/metadata - Métadonnées

    DELETE /files/{id} - Supprimer

📄 Livrables

    Code API complète

    Docker Compose fonctionnel

    Tests Postman

    Rapport architecture
