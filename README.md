# Senior Living Truth Series

Production-oriented Django application for managing educational seminars, community events, attendee relationships, registrations, communications, and operational reporting.

The project combines a public-facing event experience with a purpose-built administrative workflow. Staff can publish event content, manage locations and partners, track attendance, maintain attendee records, send registration confirmations, and export operational data for use outside the application.

## Highlights

- **Public event experience**
  - Home page with upcoming North and South series events
  - Year-based seminar schedules
  - Seminar recording archive
  - Tours and Expert Insights event types
  - Education partners, FAQs, testimonials, About, Terms, and Privacy pages
  - Responsive Tailwind CSS interface

- **Registration workflow**
  - Registration for seminars and other events
  - Optional spouse registration
  - Duplicate-aware attendee lookup and creation
  - Phone normalization and form-level validation
  - Registration confirmation email with event and location details
  - Service-to-service registration endpoint for automated workflows

- **Administrative operations**
  - Rich event and partner content management
  - Location and event-series management
  - Attendee search, filtering, tagging, and relationship tracking
  - Registration status actions for registered, attended, and cancelled records
  - Attendance summaries embedded in admin views
  - Export tools for sign-in sheets, nametags, attendee data, filtered attendees, and analytics

- **Maintainability**
  - Django ORM query managers for common event and attendee queries
  - Reusable service functions for email, CSV, registration, and validation workflows
  - Environment-driven configuration
  - Automated Django test coverage for forms, models, services, views, exports, and API behavior

## Technology

| Area | Technology |
| --- | --- |
| Application | Python, Django |
| Database | PostgreSQL in deployment; SQLite may be used for local development |
| UI | Django templates, Tailwind CSS |
| Administration | Django Admin, Jazzmin, DaisyUI |
| Content editing | Django Summernote |
| Integrations | SendGrid-compatible email delivery and authenticated registration API |
| Supporting packages | django-environ, django-localflavor, django-phonenumber-field, django-taggit, Pillow |

## Architecture at a glance

The application is organized as a conventional Django project:

```text
config/                 Project settings, URL configuration, ASGI/WSGI entrypoints
slts/
  models.py             Events, attendees, registrations, locations, partners, FAQs
  forms.py              Public registration form validation
  services.py           Registration, email, phone, and CSV service layer
  views.py              Public pages and registration/API endpoints
  admin.py              Staff administration and operational actions
  admin_views.py        Staff-only export endpoints
  templates/            Public and administrative presentation
  migrations/           Versioned database schema
tailwind/               Tailwind source and build configuration
static/                 Compiled and static assets
manage.py               Django command-line entrypoint
```

## Local development

### Prerequisites

- Python 3.12 or newer
- Node.js and npm
- A PostgreSQL database for production-like development, or SQLite for a lightweight local environment

### 1. Create a Python environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd tailwind
npm install
cd ..
```

### 3. Configure the environment

Copy the example configuration and replace every placeholder with local values:

```bash
cp env.example .env
```

The application reads database, email, host, static-file, media, and site URL settings from `.env`. Keep `.env`, local databases, uploaded media, and other runtime data outside version control. Never use example credentials in a deployed environment.

### 4. Initialize the database

```bash
python manage.py migrate
```

Create an administrative account when needed:

```bash
python manage.py createsuperuser
```

### 5. Build and run the application

Build the compiled stylesheet:

```bash
npm --prefix tailwind run build
```

Start the development server:

```bash
python manage.py runserver
```

For active Tailwind development, run the watcher in a second terminal:

```bash
npm --prefix tailwind run watch
```

## Testing and quality checks

Run Django’s system checks and the full application test suite:

```bash
python manage.py check
python manage.py test
```

The test suite covers:

- Registration form validation
- Attendee relationship synchronization
- Event query and filtering behavior
- Confirmation email content
- CSV export formats and ordering
- Public schedule and registration flows
- Authenticated API registration behavior

Before opening a pull request, also rebuild the frontend assets when Tailwind source files have changed:

```bash
npm --prefix tailwind run build
```

## Deployment notes

Production configuration should provide:

- A strong, unique Django secret key
- `DEBUG=False`
- Explicit production `ALLOWED_HOSTS`
- PostgreSQL connection settings
- Secure email provider settings
- Persistent static and media storage
- A production WSGI/ASGI process manager such as Gunicorn

Typical deployment steps are:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

The deployment environment—not the repository—should provide secrets and user-generated data. Do not commit `.env`, `db.sqlite3`, uploaded media, or generated deployment artifacts.

## Operational data exports

Authorized staff can export:

- Seminar sign-in sheets
- Seminar nametags
- Seminar attendee detail
- Filtered attendee lists
- Complete attendee lists
- Registration and attendance analytics by year and event type

These exports can contain personal information. Treat generated CSV files as confidential operational data and store or transmit them using the organization’s approved controls.

## Project conventions

- Keep business logic in model managers, forms, or services rather than duplicating it in templates.
- Use migrations for every schema change.
- Add or update tests when changing registration, attendee, event, export, or integration behavior.
- Keep environment-specific configuration outside source control.
- Review authorization and personal-data implications for every new administrative or export feature.

## License and ownership

This repository is presented as a portfolio and engineering project. Add the organization’s preferred license and contribution terms before accepting external contributions or distributing the application for reuse.
