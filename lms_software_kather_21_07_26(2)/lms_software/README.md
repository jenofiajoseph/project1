# Secure Flask Admin System (White & Blue UI)

This project provides a secure Administrator Login and Logout system built with Python Flask, PostgreSQL, Bootstrap 5, HTML, CSS, and JavaScript. The admin password is encrypted using secure PBKDF2 hashing in the database.

## Tech Stack
*   **Backend:** Python Flask, Flask-SQLAlchemy (ORM)
*   **Database:** PostgreSQL (with `psycopg2-binary`)
*   **Password Hashing:** Werkzeug Security (PBKDF2 with SHA256)
*   **Frontend:** Bootstrap 5, FontAwesome 6, custom CSS & JS
*   **Theme:** White backgrounds with royal blue and light blue accents

---

## Installation & Setup

### 1. Prerequisites
Ensure you have the following installed on your machine:
*   [Python 3.10+](https://www.python.org/downloads/)
*   [PostgreSQL Database](https://www.postgresql.org/download/)

### 2. Create the Database
Open your PostgreSQL terminal (pgAdmin, psql, etc.) and create a new database:
```sql
CREATE DATABASE lms_db;
```

### 3. Configure Environment Variables
Copy the `.env.example` file to a new file named `.env`:
```bash
copy .env.example .env
```
Open `.env` in a text editor and update the database connection details to match your system. For example:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/lms_db
SECRET_KEY=some-really-strong-secret-key-12345
```

### 4. Create and Activate Virtual Environment
Initialize a local Python virtual environment to manage dependencies securely without globally contaminating packages:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 5. Install Dependencies
Install all the required Python packages inside the active virtual environment:
```bash
pip install -r requirements.txt
```

### 6. Initialize & Seed Database
Run the initialization script. This creates the PostgreSQL tables and seeds a default administrator user:
```bash
python init_db.py
```
This script will output confirmation details:
*   **Admin Username:** `admin`
*   **Admin Password:** `admin123` *(stored in PostgreSQL database as a cryptographically secure hash)*

---

## Running the Application

Start the Flask development server:
```bash
python app.py
```

The application will launch in debug mode. Open your browser and navigate to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## Features Implemented

1.  **Hashed Admin Password:**
    *   Passwords are never stored in plain text.
    *   Werkzeug's `generate_password_hash` hashes the password securely during seeding.
    *   During login, `check_password_hash` compares the request password with the hashed db record.
2.  **Session Security:**
    *   Admin sessions are cryptographically signed using Flask's `SECRET_KEY`.
    *   The dashboard route `/dashboard` is protected, redirecting unauthenticated users to `/login`.
3.  **Clean White & Blue UI:**
    *   Modern light layout with deep royal blue accents.
    *   Card layouts with soft drop-shadows.
    *   Custom password visibility show/hide toggle.
    *   Interactive hover states and transitions on buttons.
