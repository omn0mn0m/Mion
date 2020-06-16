# Mion
 Anime Watch Club utilities

## Installation
Mion is configured to run on Heroku.

### Local Installation
For easy local installation, only Docker and Docker-Compose are required.

To set up locally, run the following commands:

```
docker-compose run web python manage.py makemigrations awc
docker-compose run web python manage.py migrate
docker-compose up
```

## Environment Variables
Environment variables can be set using `export VARIABLE_NAME=VALUE`.

The following environment variables should be set in production for Django:

- DJANGO_SECRET_KEY
- DJANGO_DEBUG

The following environment variables should be set in production for PostgreSQL:

- DJANGO_POSTGRES_NAME
- DJANGO_POSTGRES_USER
- DJANGO_POSTGRES_PASSWORD
- DJANGO_POSTGRES_HOST
- DJANGO_POSTGRES_PORT
