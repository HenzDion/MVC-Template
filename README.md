# Fieldnote User Profiles

A simple user-profile management system with three clients sharing one API:

- **Backend:** Express REST API with PostgreSQL.
- **Web app:** Vue 3 and Vite.
- **Desktop app:** Python Tkinter.

## Requirements

- Node.js 18 or later and npm.
- PostgreSQL, with `psql` available in PowerShell.
- Python 3.10 or later with Tkinter enabled for the desktop app.

## First-time Setup

Run these commands from the project root in PowerShell.

### 1. Create the database

Create the database once. If it already exists, skip this command:

```powershell
psql -U postgres -c "CREATE DATABASE user_profiles;"
```

Apply the schema:

```powershell
psql -U postgres -d user_profiles -f backend/src/db/schema.sql
```

If PostgreSQL uses a different role or database name on your machine, update the commands and connection string to match.

### 2. Configure and install the backend

The backend reads `DATABASE_URL` from `backend/.env`. If that file does not exist, create it from the example:

```powershell
Copy-Item backend/.env.example backend/.env
```

Edit `backend/.env` and set `DATABASE_URL` to your PostgreSQL connection, for example:

```text
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/user_profiles
```

Keep your real `.env` credentials private. Install the backend packages:

```powershell
Set-Location backend
npm install
Set-Location ..
```

## Run the System

Keep each service running in its own terminal. Start the backend before using either client.

### Backend API

From the project root:

```powershell
Set-Location backend
npm run dev
```

The API listens on `http://localhost:3000`. For a non-development start, use `npm start` instead.

### Vue web app

Open another terminal at the project root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`. The development server proxies `/api` requests to `http://localhost:3000`.

### Tkinter desktop app

Open another terminal at the project root. No Python packages need to be installed:

```powershell
py desktop/app.py
```

The desktop client also uses `http://localhost:3000/api/users` by default. To change the API URL for the desktop app:

```powershell
$env:USER_PROFILE_API_URL = "http://localhost:3000/api/users"
py desktop/app.py
```

## API Reference

All routes use the `/api/users` prefix. Responses for successful reads and writes use a `{ "data": ... }` envelope; deletion returns `204 No Content`.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/users` | List profiles |
| `GET` | `/api/users/:id` | Read one profile |
| `POST` | `/api/users` | Create a profile |
| `PATCH` | `/api/users/:id` | Update profile fields |
| `DELETE` | `/api/users/:id` | Delete a profile |

Profile fields are `firstName`, `lastName`, `email`, `phone`, `bio`, and `avatarUrl`. `firstName`, `lastName`, and `email` are required when creating a profile. Emails must be unique.

Example request body:

```json
{
  "firstName": "Ada",
  "lastName": "Lovelace",
  "email": "ada@example.com",
  "phone": "+1-555-0100",
  "bio": "Mathematician and writer",
  "avatarUrl": "https://example.com/ada.jpg"
}
```

## Troubleshooting

- **The clients cannot reach the API:** Check that the backend terminal says it is listening on port `3000`.
- **Profile requests fail:** Check that PostgreSQL is running, `backend/.env` has the correct `DATABASE_URL`, and the schema was applied to that database.
- **The web app uses another API host:** Set `VITE_API_PROXY_TARGET` before starting Vite, for example `$env:VITE_API_PROXY_TARGET = "http://localhost:3000"`.
- **The desktop app cannot start:** Use a Python installation with Tkinter enabled. On Windows, the standard python.org installer includes Tcl/Tk.

## Project Structure

```text
backend/   Express API, PostgreSQL model, and SQL schema
frontend/  Vue 3 web client
desktop/   Tkinter desktop client
```