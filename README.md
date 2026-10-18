# Django Portfolio

A Django portfolio featuring a personal introduction, professional experience,
selected projects, and personal writing. Built with server-rendered HTML
templates and CSS.

## How Django Works

Django connects incoming requests to Python code, can read and write database
records, and can render HTML for the browser.

### The Main Pieces

| Term               | Meaning                                                                                            | In this project                                                                                                                                      |
| ------------------ | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project            | The configuration and apps that make up the website.                                               | `portfolio/` holds shared configuration.                                                                                                           |
| App                | A Python package for related features—not necessarily one page. Apps do not need database models. | `pages` handles the portfolio pages and experience records; `blogs` handles personal posts, topics, and archives.                                |
| Settings           | Configuration for databases, apps, templates, languages, and file paths.                           | `portfolio/settings.py`; apps are registered in `INSTALLED_APPS`.                                                                                |
| URL route          | Maps a URL path to a view.                                                                         | `portfolio/urls.py` maps `/projects/` to the Projects view.                                                                                      |
| View               | Python code that handles a request and returns a response—not the visual layout.                  | `pages/views.py` queries and filters project records.                                                                                              |
| Template           | HTML with placeholders, loops, and conditions for displaying data.                                 | Page templates extend `templates/base.html`, which supplies the shared header and footer.                                                           |
| Model              | A Python class describing database-backed data. Django's ORM lets you query it with Python.        | `Project` and `ProjectTranslation` represent projects; `Experience` represents roles; `BlogPost` represents writing. Home uses JSON instead. |
| Migration          | A versioned description of changes to database structure or data.                                  | Files in each app's `migrations/` directory.                                                                                                        |
| Management command | A terminal task run through `manage.py`.                                                          | Built-in commands include `runserver` and `test`; custom commands live in an app's `management/commands/` directory.                            |

### Request Flow

```text
Example request: /projects/?q=Kafka

1. The browser sends the request to Django.
2. portfolio/urls.py selects the Projects view.
3. The view in pages/views.py queries published projects and selects translated text.
4. The view filters the displayed text and shared fields using the search query.
5. The template renders the cards inside the shared base layout.
6. Django returns HTML to the browser.
```

### Changing the Database

1. Edit a model in `models.py`.
2. Run `python manage.py makemigrations` to generate migration files. This does
   not change the database yet.
3. Review the generated files, then run `python manage.py migrate` to apply
   pending migrations. Django records which migrations have been applied.
4. Run tests and commit the model changes together with their migrations.

Template, CSS, and JSON edits do not require migrations. Migration files
normally belong in Git; the local database does not. Review data migrations
for private records before committing, and avoid deleting applied migrations
just because they look old.

## Local Development

### First-Time Setup

Run these commands from the repository root:

```zsh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Copy the environment example only if you do not already have a `.env` file.
Edit `.env` to set your local `DJANGO_SECRET_KEY`, then initialize the database
and compile the interface translations before starting the server.
Translation compilation requires GNU gettext (`brew install gettext` on macOS).

```zsh
python manage.py migrate
python manage.py compilemessages --ignore=.venv
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Stop the server with `Control-C`.

A fresh database starts without project or experience records; migrations
create the tables, not your personal content.

### Returning to the Project

```zsh
source .venv/bin/activate
python manage.py runserver
```

Run migrations again when new migration files are added. Install requirements again when dependencies change.

### Testing

Tests live in each app’s `tests/` directory and use fictional content.

```zsh
# Test the currently enabled apps
python manage.py test pages portfolio

# Test Experience only
python manage.py test pages.tests.test_experience
```

## Configuration and Content

### Environment and Shared Profile

`.env.example` documents the environment variables. Your local `.env` contains the secret key, database settings, and shared profile values such as your name, profession, email, and social links.

To offer your resume, place a public-facing PDF at `media/resume.pdf`, or set `PORTFOLIO_RESUME_FILE` to another local path in `.env`. The buttons are hidden when the file is missing. The PDF stays outside Git but is publicly accessible through the site, so include only contact details you want to share.

SQLite is the default database. To use PostgreSQL instead, set
`PORTFOLIO_DB_ENGINE=postgresql` and configure the `POSTGRES_*` variables.

### Homepage Content

Home uses a generic JSON example by default. To customize it, copy the example once:

```zsh
mkdir -p private
cp examples/home.json private/home.json
```

Do not overwrite the file if you have already customized it. Set this path in `.env`:

```dotenv
PORTFOLIO_HOME_CONTENT_FILE=private/home.json
```

JSON content changes appear on the next request. Changes to `.env` require
restarting the server. Text is escaped and rendered as plain text, not HTML.

Edit the heading, location, description, and paragraphs in `private/home.json`.
For a photo, place the file under `media/` and set `headshot_path` to its relative
path, such as `images/headshot.jpg`. Leave that path empty to omit the photo.

### Projects

Projects are stored in the database and edited under `/admin/pages/project/`.
Each project has a shared English title, repository URL, technologies, and
publication flag. Translation forms hold the English, Spanish, and French
categories and descriptions. Published projects need English text; missing
Spanish or French text falls back to English.

The public page reads the database. Cards are sorted
alphabetically by the shared English title. Links must point to HTTPS GitHub
repositories. Search matches the title, displayed category and description,
and technologies, ignoring case and accents, and works without JavaScript.

### Experience

Experience records are stored in the database and edited under
`/admin/pages/experience/`. Company details, dates, technologies, logos, and
slugs are shared across languages. Translation forms hold the role, location,
overview, and highlights. Only published records with English text appear;
missing Spanish or French translations fall back to English.

`display_order` controls the list order, with lower numbers first. Each record
has a unique slug for its detail URL, such as `/experience/example-company/`.
Admin suggests a slug from the company name, but it can be edited. The slug
`resume` is reserved for the PDF route. Keep slugs stable once links are shared.

Enter one highlight per line. To embed a link, use `[label](https://example.com/)`;
raw HTML is escaped. Uploaded logos live under `media/`, outside Git.

### Static and Media Files

The browser requests stylesheets and images separately from the page HTML.

Shared CSS lives in `static/`, while page-specific CSS lives in `pages/static/pages/`.
Personal images live in `media/` and stay outside Git.

### Languages

The language selector supports English, French, and Spanish. Django remembers
the selection in a cookie without changing page URLs. Translations are supplied
manually; text is not automatically translated.

To translate the homepage, add an optional `translations` object to
`private/home.json`, keyed by `fr` and `es`. Each translation contains
`heading`, `location`, `description`, and a `paragraphs` list, just like the
English text at the top level. Projects and Experience store translations in
the database. Missing translations fall back to English; project names, company
names, and the headshot remain unchanged. Posts and resume text remain English
for now.

Interface translations, such as navigation labels and buttons, live in
`locale/<language>/LC_MESSAGES/django.po`. Keep personal content in private JSON
files or database records, not in these catalogs. Compile the catalogs after
cloning, after editing `.po` files, and during deployment; the generated `.mo`
files are ignored by Git:

```zsh
python manage.py compilemessages --ignore=.venv
```

See Useful Django Commands below for updating the translation catalogs.

## Before Deployment

`runserver` is for development, not production. Use a suitable production
server and configure static and media file serving.

Provide a unique `DJANGO_SECRET_KEY`, disable `DJANGO_DEBUG`, set
`DJANGO_ALLOWED_HOSTS` for the deployed domain, and configure HTTPS and secure
cookies. Supply your private content and environment configuration separately
from the public repository.

## Privacy and Version Control

`.env`, `private/`, `media/`, and the local database are ignored. The reusable
code, templates, and generic examples can be committed without your personal
content.

This keeps personal content out of the repository, not out of the rendered
website. Anything displayed on a public page is still public.

## Useful Django Commands

| Command                              | Purpose                                              |
| ------------------------------------ | ---------------------------------------------------- |
| `python manage.py runserver`       | Start the local development server.                  |
| `python manage.py check`           | Check Django configuration for common problems.      |
| `python manage.py test pages portfolio` | Test the currently enabled apps.                  |
| `python manage.py createsuperuser` | Create an account for Django's admin interface.      |
| `python manage.py makemigrations`  | Generate migration files after model changes.        |
| `python manage.py migrate`         | Apply pending migrations to the configured database. |
| `python manage.py showmigrations`  | Show migrations and whether they have been applied.  |
| `python manage.py shell`           | Open a Python shell with Django configured.          |
| `python manage.py makemessages -l fr -l es --ignore=.venv --ignore=private --ignore=media` | Update French and Spanish interface translation catalogs. |
| `python manage.py compilemessages --ignore=.venv` | Compile interface translations for Django to use. |
