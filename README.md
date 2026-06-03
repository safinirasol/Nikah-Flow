# Nikah Solemnisation Management System

A Django-based web application for managing nikah solemnisation applications, bookings, imam schedules, and monthly reports.

## Description

This repository contains a custom Django project named `SOLEMNISATION_WESBITE` with a single app, `NikahFlow`, built to manage the marriage application workflow for brides/grooms, administrators, and imams.

The system supports:
- bride/groom application submission with uploaded ID, HIV, and marriage course documents
- imam availability scheduling and assignment
- administrator user management, booking approval, and report generation
- bride/groom booking tracking and application status monitoring

## Features

- custom user roles: `bridegroom`, `imam`, and `adminchairman`
- secure file uploads for identity documents and consent forms
- booking and application approval/rejection flow
- imam assignment for approved bookings
- monthly report generation
- SQLite database backend and local media file storage

## Technology Stack

- Python
- Django 5.0.7
- SQLite3

## Installation

1. Create a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install Django:
   ```powershell
   pip install django==5.0.7
   ```
3. Apply migrations:
   ```powershell
   python manage.py migrate
   ```
4. Start the development server:
   ```powershell
   python manage.py runserver
   ```
5. Open the app in your browser:
   ```text
   http://127.0.0.1:8000/homepage/
   ```

## Project Structure

- `SOLEMNISATION_WESBITE/` - Django project settings and URL configuration
- `NikahFlow/` - main application containing models, views, templates, and static files
- `db.sqlite3` - local SQLite database file
- `media/` - uploaded application and booking documents

## Important Notes

- The app uses a custom `User` model in `NikahFlow/models.py` and session-based login in `NikahFlow/views.py`.
- Admin and imam accounts require pre-defined IDs:
  - Admin ID: `adminmasjid0411`
  - Imam ID: `imammasjid1104`
- Debug mode is enabled in `SOLEMNISATION_WESBITE/settings.py`; this project should be hardened before production use.

## Useful URLs

- `/homepage/` - main public homepage
- `/homepage/signup/` - user registration
- `/homepage/login/` - login page
- `/homepage/account/admin/` - admin dashboard
- `/homepage/account/imam/` - imam dashboard
- `/homepage/account/bridegroom/` - bride/groom dashboard

## License

This repository does not include a license file by default. Add a license if you plan to publish or share this project publicly.
