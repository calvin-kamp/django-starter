# django-starter

Template for Django REST backends with authentication already built in.
Runs with Docker and PostgreSQL. The frontend is not part of this repository
and can be any framework.

## Contents

- [What's included](#whats-included)
- [Requirements](#requirements)
- [Setup](#setup)
  1. [Create the project](#1-create-the-project)
  2. [Rename the project](#2-rename-the-project)
  3. [Create the local Python environment](#3-create-the-local-python-environment)
  4. [Create the `.env`](#4-create-the-env)
  5. [Customize the user model (optional)](#5-customize-the-user-model-optional)
  6. [Create the migrations](#6-create-the-migrations)
  7. [Start](#7-start)
- [Development](#development)
  - [What runs where](#what-runs-where)
  - [Create a new app](#create-a-new-app)
  - [Change models](#change-models)
  - [Add a package](#add-a-package)
- [Production](#production)
- [Environment variables](#environment-variables)
- [Auth API](#auth-api)
- [Email activation](#email-activation)
- [Email](#email)
- [Redis](#redis)
- [Project structure](#project-structure)
- [Commands](#commands)
- [License](#license)

## What's included

- Django 6.1, Django REST Framework, PostgreSQL 17, Redis 8
- Custom user model (`app_auth.User`, login with username), ready to extend
- JWT authentication with `HttpOnly` cookies (no tokens in the response body)
- Register, login, logout, token refresh
- Optional email activation after registration (switch in `.env`)
- Configuration via `.env` ([django-environ](https://django-environ.readthedocs.io/))
- gunicorn and WhiteNoise for production, `runserver` for development

## Requirements

- Docker with Docker Compose: runs the API, the database and Redis
- Python 3.13: for commands that create files (new apps, migrations), see
  [Development](#development)

## Setup

### 1. Create the project

Create a new repository from this template on GitHub ("Use this template")
and clone it.

### 2. Rename the project

The name `django-starter` belongs to the template. Replace it with the name
of your project:

| File           | What                                                                                                                         |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `compose.yaml` | `container_name` of `db`, `redis` and `api`. With the same names, two projects from this template can't run at the same time |
| `README.md`    | Title and description                                                                                                        |
| `LICENSE`      | Copyright holder, or a different license                                                                                     |

### 3. Create the local Python environment

```sh
python -m venv .venv
```

Activate it:

```sh
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install the packages:

```sh
pip install -r requirements.txt
```

### 4. Create the `.env`

```sh
cp .env.template .env
```

Fill in at least:

| Variable                                            | Value                                                    |
| --------------------------------------------------- | -------------------------------------------------------- |
| `SECRET_KEY`                                        | Long random string                                       |
| `JWT_SIGNING_KEY`                                   | Another long random string                               |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database name, user, password                            |
| `DATABASE_URL`                                      | Same values: `postgres://<user>:<password>@db:5432/<db>` |

Generate a random string:

```sh
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

For local development additionally:

```env
DEBUG=True
AUTH_COOKIE_SECURE=False
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

`CORS_ALLOWED_ORIGINS` is the address of your frontend dev server.

### 5. Customize the user model (optional)

`app_auth.User` works like Django's default user: login with username and
password. It can be changed now, before the first migration. Later changes
are possible too, but need migrations for existing data.

Add fields, e.g. a profile picture:

1. Add the field to `User` in `app_auth/models.py`.
2. Show it in the admin: `fieldsets` in `app_auth/admin.py`.
3. Return it in the API: `fields` of `UserSerializer` in
   `app_auth/api/serializers.py`.

The docstrings in these files show examples.

Larger changes, e.g. login with email instead of username, also affect
`UserManager` in `app_auth/models.py` and `RegisterSerializer` and
`LoginSerializer` in `app_auth/api/serializers.py`.

### 6. Create the migrations

The migrations of `app_auth` are not part of the template. When the user
model is final, run once:

```sh
python manage.py makemigrations app_auth
```

This must happen before the first `docker compose up`. The container runs
`migrate` on every start and fails without these migrations.

### 7. Start

```sh
docker compose up --build
```

The API runs on <http://localhost:8000>, the admin on
<http://localhost:8000/admin/>.

Create an admin user:

```sh
docker compose exec api python manage.py createsuperuser
```

## Development

### What runs where

API, database and Redis run in Docker. `docker compose up` automatically
loads `compose.override.yaml` as well:

- `runserver` with auto-reload instead of gunicorn
- Project folder mounted into the container, code changes apply without a rebuild
- PostgreSQL reachable on `localhost:5432`, Redis on `localhost:6379`

Commands run in two places:

| Where                                     | Commands                                      | Why                                                                                                    |
| ----------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Local, with active `.venv`                | `startapp`, `makemigrations`, `pip install`   | They create or change files. Locally the files belong to your user and land directly in the repository |
| Container (`docker compose exec api ...`) | `migrate`, `createsuperuser`, `shell`, `test` | They need the database                                                                                 |

Files created in the container also appear in the project folder because of
the mount. On Linux they belong to `root` and can't be edited without `sudo`.

`.env` points to the database host `db`, which only exists inside Docker.
Locally, `makemigrations` therefore prints a warning about the migration
history. The migrations are created anyway.

### Create a new app

1. Create the app:

   ```sh
   python manage.py startapp app_<name>
   ```

2. Create the folder `app_<name>/api/` with `urls.py`, `serializers.py` and
   `views.py`, like in `app_auth`.
3. Add `"app_<name>"` to `INSTALLED_APPS` in `core/settings.py`.
4. Include the URLs in `core/urls.py`:

   ```python
   path("<name>/", include("app_<name>.api.urls")),
   ```

5. Write the models, then create and apply the migrations (see below).

### Change models

```sh
python manage.py makemigrations
docker compose exec api python manage.py migrate
```

Commit the new files in `migrations/`.

### Add a package

```sh
pip install <package>
pip freeze > requirements.txt
docker compose up -d --build
```

The rebuild installs the package in the container as well.

## Production

Production uses only `compose.yaml`:

```sh
docker compose -f compose.yaml up -d --build
```

On every start the container runs `migrate`, and with `DEBUG=False` also
`collectstatic`.

Production `.env`:

- `DEBUG=False`
- `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set to the real domains
- `AUTH_COOKIE_SECURE=True`
- `USE_X_FORWARDED_PROTO=True` only behind a reverse proxy that terminates
  HTTPS and sets the `X-Forwarded-Proto` header itself
- SMTP settings (see [Email](#email))

After changes to `.env`, recreate the container with `docker compose up -d`.
`docker compose restart` does not read the `.env` again.

## Environment variables

| Variable                                            | Default                   | Purpose                                                                                                 |
| --------------------------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------- |
| `SECRET_KEY`                                        | required                  | Django secret key                                                                                       |
| `DEBUG`                                             | `False`                   | Debug mode, only for development                                                                        |
| `ALLOWED_HOSTS`                                     | empty                     | Domains the API answers to, comma-separated                                                             |
| `CSRF_TRUSTED_ORIGINS`                              | empty                     | Trusted origins for the admin, e.g. `https://api.example.com`                                           |
| `USE_X_FORWARDED_PROTO`                             | `False`                   | Trust the HTTPS header of the reverse proxy                                                             |
| `CORS_ALLOWED_ORIGINS`                              | empty                     | Frontend origins that may call the API, comma-separated                                                 |
| `JWT_SIGNING_KEY`                                   | `SECRET_KEY`              | Key for the JWTs                                                                                        |
| `AUTH_COOKIE_SECURE`                                | `True`                    | Send cookies only over HTTPS, `False` for local HTTP                                                    |
| `FRONTEND_BASE_URL`                                 | empty                     | Address of the frontend incl. scheme and port, e.g. `http://localhost:5173`. Links in emails point here |
| `AUTH_EMAIL_ACTIVATION`                             | `False`                   | Email activation after registration, see below                                                          |
| `AUTH_ACTIVATION_PATH`                              | `/activate/{uid}/{token}` | Path of the activation page in the frontend                                                             |
| `PASSWORD_RESET_TIMEOUT`                            | `259200`                  | Validity of activation links in seconds (3 days)                                                        |
| `DEFAULT_FROM_EMAIL`                                | `noreply@localhost`       | Sender of all emails                                                                                    |
| `EMAIL_BACKEND`                                     | console backend           | Mail backend, see [Email](#email)                                                                       |
| `EMAIL_HOST`                                        | required for SMTP         | SMTP server                                                                                             |
| `EMAIL_PORT`                                        | `587`                     | SMTP port                                                                                               |
| `EMAIL_HOST_USER`                                   | empty                     | SMTP user                                                                                               |
| `EMAIL_HOST_PASSWORD`                               | empty                     | SMTP password                                                                                           |
| `EMAIL_USE_TLS`                                     | `True`                    | TLS for SMTP                                                                                            |
| `DATABASE_URL`                                      | required                  | Database connection                                                                                     |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | required                  | Used by the `db` container                                                                              |

## Auth API

All endpoints are below `/auth/`.

| Method | Path                               | Body                            | Result                                                                        |
| ------ | ---------------------------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| POST   | `/auth/register/`                  | `username`, `email`, `password` | 201. Without email activation: logged in (cookies set)                        |
| POST   | `/auth/activate/<uidb64>/<token>/` | none                            | 200, account active and logged in. 400: link invalid, expired or already used |
| POST   | `/auth/login/`                     | `username`, `password`          | 200, cookies set. 401: wrong credentials or account not active                |
| POST   | `/auth/logout/`                    | none                            | 200, cookies deleted, refresh token invalid                                   |
| POST   | `/auth/token/refresh/`             | none                            | 200, new cookies. 401: refresh cookie missing or invalid                      |

Successful responses contain `detail` and, except logout and refresh, `user`
(`id`, `username`, `email`).

### Cookies

| Cookie          | Path     | Lifetime   |
| --------------- | -------- | ---------- |
| `access_token`  | `/`      | 15 minutes |
| `refresh_token` | `/auth/` | 7 days     |

Both are `HttpOnly` and `SameSite=Lax`. The frontend must send every request
with credentials (e.g. `fetch(..., { credentials: "include" })`), otherwise
the browser neither stores nor sends the cookies. When a request returns 401,
the frontend calls `/auth/token/refresh/` and repeats the request.

Every endpoint requires a logged-in user. Public views set
`permission_classes = (AllowAny,)` themselves.

## Email activation

With `AUTH_EMAIL_ACTIVATION=False` a new user is active and logged in right
after registration.

With `AUTH_EMAIL_ACTIVATION=True`:

1. Registration creates an inactive user and sends an email with a link to
   `FRONTEND_BASE_URL` + `AUTH_ACTIVATION_PATH`.
2. The frontend page reads `uid` and `token` from its URL and sends
   `POST /auth/activate/<uid>/<token>/`.
3. The backend activates the user and sets the auth cookies.

Each link works once. Login is not possible before the activation.
If `FRONTEND_BASE_URL` is empty, Django refuses to start.

## Email

In development the console backend prints all emails to the container log:

```sh
docker compose logs -f api
```

In production set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
```

## Redis

Redis runs as the service `redis`. Its data is stored in the volume
`redis_data`.

| From                | Address                  |
| ------------------- | ------------------------ |
| API container       | `redis://redis:6379`     |
| Local (development) | `redis://localhost:6379` |

The template itself doesn't use Redis yet. Projects can use it e.g. as
Django cache or as Celery broker.

## Project structure

```text
core/               Project settings and root URLs
app_auth/           User model and admin
app_auth/api/       Auth endpoints: views, serializers, cookies, tokens
compose.yaml        db, redis and api (production)
compose.override.yaml  Development additions
entrypoint.sh       Runs migrate (and collectstatic) on container start
```

New apps get the prefix `app_` and their own `api/` folder like `app_auth`.
How to add fields to the user model is described in `app_auth/models.py`.

## Commands

| Task                                     | Command                                                       |
| ---------------------------------------- | ------------------------------------------------------------- |
| New migrations (local)                   | `python manage.py makemigrations`                             |
| Apply migrations                         | `docker compose exec api python manage.py migrate`            |
| Run tests                                | `docker compose exec api python manage.py test`               |
| Django shell                             | `docker compose exec api python manage.py shell`              |
| Remove expired tokens from the blacklist | `docker compose exec api python manage.py flushexpiredtokens` |

`flushexpiredtokens` should run regularly in production, e.g. daily via cron.

## License

[MIT](LICENSE)
