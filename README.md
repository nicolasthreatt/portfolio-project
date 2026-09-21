# Nicolas Threatt Portfolio

This is a Django portfolio site with three focused sections:

- Home: a personal introduction at `/`
- Blogs: personal writing at `/blogs/`
- Experience: professional roles at `/experience/`
- Projects: selected repositories at `/projects/`
- Resume: a formatted resume at `/resume/`

The Django apps are intentionally small:

- `home` renders Home and Projects.
- `blogs` owns personal posts, topics, and professional experiences.
- `resume` renders the resume page.

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

# Restore the bundled experience records and logos
python manage.py seed_legacy_experience
```

## Environment configuration

`.env` is deliberately ignored by Git. It holds your local secret key and any
database credentials. The included `.env.example` documents the supported
settings. SQLite is used by default; set `PORTFOLIO_DB_ENGINE=postgresql` and
the `POSTGRES_*` values only when you intentionally want to use PostgreSQL.

Before deployment, provide a unique `DJANGO_SECRET_KEY`, turn off
`DJANGO_DEBUG`, set the allowed hosts for the deployed domain, and configure
HTTPS/security-cookie settings at the hosting layer or in Django settings.
