# Fieldnote Desktop

A Tkinter desktop client for the Express user-profile API in `../backend`. It uses only Python's standard library.

## Run

1. Start the backend from `../backend` with `npm run dev`.
2. Run this app with Python 3.10 or later:

```powershell
py desktop/app.py
```

Run the command from the project root. The default API URL is `http://localhost:3000/api/users`.

To use another API URL, set `USER_PROFILE_API_URL` before starting the app:

```powershell
$env:USER_PROFILE_API_URL = "http://localhost:3000/api/users"
py desktop/app.py
```

The app supports listing, searching, creating, editing, and deleting profiles. It sends the backend's `firstName`, `lastName`, `email`, `phone`, `bio`, and `avatarUrl` fields and keeps HTTP work off the Tkinter event loop.