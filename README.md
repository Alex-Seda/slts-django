# System Package Prerequisites
- Python
- Node.js
- Node Package Manager (npm)

---

# Installation Steps (from project root dir)
1. Set up a virtual environment (venv) to isolate project python packages from system python packages
```bash 
python -m venv venv
```
2. Enter venv
```bash 
source venv/bin/activate
```
3. Install necessary Django Python packages in venv
```bash
pip install \
django \
django-environ \
django-localflavor \
django-phonenumbers \
django-phonenumber-field \
django-summernote \
django-widget-tweaks \
django-jazzmin \
pillow \
gunicorn psycopg[binary]
```
4. Install node modules for Tailwind CSS
```bash
cd tailwind && npm install && cd ..
```

*NOTE: If you update your system, it will break venv. The easiest solution is to just remove the venv directory and run through steps 1-3 again. This happens because venv is tightly tied with symlinks to the specific version python binaries on your system. When these binaries are updated, the links break.*

*TLDR: After a system update, remove venv and reinstall using steps 1-3.*

---

# Development Workflow

## To begin working
1. Pull GitHub changes
2. Run migrations (if models were updated)
```bash
    python manage.py makemigrations
    python manage.py migrate
```
3. Update venv packages (run the updated pip install command above, it will ignore all packages you already have)
4. Download your development backups
    - This is only needed if you are working on different machines
    - If you save the media/images, static/images, .env, and db.sqlite3 to a safe location, you can just download them to effectively have the same dev environment everywhere

## Live Updates
1. Bring the live server up

    Run the below command in Project Root
```bash
    python manage.py runserver
```
2. Ensure Tailwind CSS autocompiles with changes

    Run the below command in the Tailwind directory
```bash
    npm run watch
```

*Leave the window for each command open so that they continue running until you are done working*


## When finished
1. Save 
Press Ctrl+C on both running commands to quit them

