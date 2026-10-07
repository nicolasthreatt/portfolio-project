# Django Portfolio

This is a Django portfolio site with five sections:

- Home: a personal introduction at `/`
- Blogs: personal writing at `/blogs/`
- Experience: professional roles at `/experience/`
- Projects: selected repositories at `/projects/`
- Resume: a formatted resume at `/resume/`

The Django apps are intentionally small:

- `pages` renders Home, Projects, Experience, and Resume, and manages experience records.
- `blogs` manages personal posts, topics, and archives.

## Run locally

The development setup defaults to SQLite, so PostgreSQL is not required to get
started.

```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Stop the server with `Control-C`.

## Useful Django commands

```zsh
# Verify configuration and run tests
python manage.py check
python manage.py test

# Create an admin account, then visit /admin/
python manage.py createsuperuser

# Create database changes after editing models.py
python manage.py makemigrations
python manage.py migrate
```

## Environment configuration

`.env` is deliberately ignored by Git. It holds your local secret key and any
database credentials, plus the public profile values used by the shared templates.
The included `.env.example` documents the supported
settings. SQLite is used by default; set `PORTFOLIO_DB_ENGINE=postgresql` and
the `POSTGRES_*` values only when you intentionally want to use PostgreSQL.

## Homepage content

The homepage uses generic example content unless `PORTFOLIO_HOME_CONTENT_FILE`
points to a local JSON file. To customize it:

```zsh
mkdir -p private
cp pages/home_content.example.json private/home.json
```

Set `PORTFOLIO_HOME_CONTENT_FILE=private/home.json` in `.env`, then edit the JSON
heading, location, description, and paragraphs. For a photo, place it under `media/`
and set `headshot_path` to its relative path, such as `images/headshot.jpg`.
Leave the path empty to omit the photo.

`private/`, `media/`, and `.env` are ignored by Git. The JSON text is rendered as
plain text, not HTML. Updating the JSON takes effect on the next request;
changing the environment-file path requires restarting the server.

This separation keeps personal content out of the repository, not out of the
rendered website. Anything you display on a public website is still public.

Before deployment, provide a unique `DJANGO_SECRET_KEY`, turn off
`DJANGO_DEBUG`, set the allowed hosts for the deployed domain, and configure
HTTPS/security-cookie settings at the hosting layer or in Django settings.
