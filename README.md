# Mion

![Website](https://img.shields.io/website?down_color=lightgrey&down_message=offline&up_color=green&up_message=online&url=https%3A%2F%2Fmii-chan.herokuapp.com) ![GitHub release (latest by date including pre-releases)](https://img.shields.io/github/v/release/omn0mn0m/mion?include_prereleases) ![GitHub](https://img.shields.io/github/license/omn0mn0m/mion)

Mion is an unofficial open-source Django web application that helps manage anime and manga challenges. Mion is able to make challenge forum posts for you, edit them, and delete them. No more having to parse through a challenge code manually to add an anime to a requirement.

## Installation
Mion is configured to run on Heroku, but can also run locally.

### Local Installation
For easy local installation, only Docker and Docker-Compose are required.

To set up locally, run the following commands:

```
docker-compose run web python manage.py makemigrations awc
docker-compose run web python manage.py migrate
docker-compose up
```

## Environment Variables
The following environment variables should be set for Django:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`

The following environment variables should be set for the Anilist API:

- `ANILIST_CLIENT_ID`
- `ANILIST_CLIENT_SECRET`
- `ANILIST_REDIRECT_URI`

Environment variables can be set locally in a `.env` file in the root project directory. Environment variables can be set in production using `heroku config:set VARIABLE=VALUE`.

## Testing
To run the unit tests for this project, run the following command once before the first time you ever run a test:

`docker-compose run web python manage.py collectstatic`

For all tests, run:

`docker-compose run web python manage.py test`

## Contributing
See [CONTRIBUTING.md](https://github.com/omn0mn0m/Mion/blob/master/CONTRIBUTING.md).
