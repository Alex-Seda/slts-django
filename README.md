# System Package Prerequisites
- Python
- Django *(Possibly optional with venv?)*
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
django-localflavor \
django-phonenumbers \
django-phonenumber-field \
django-summernote
```
4. Install node modules for Tailwind CSS
```bash
cd tailwind && npm install && cd ..
```

---

# Development Workflow

## To begin working
1. Pull GitHub changes
2. Run migrations (if models were updated)
```bash
    python manage.py makemigrations
    python manage.py migrate
```

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
Press Ctrl+C on both running commands to quit them

