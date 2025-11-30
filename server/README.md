# Productivity App Backend (Flask + Sessions)

This is the Flask backend for a productivity App.  
It provides a session-based authentication system and a user-owned `Note` resource with full CRUD and pagination.

This backend was built to work in tandom with the React frontend (in the `client/` directory) via API over HTTP on port **5555**.

---

## Tech Stack

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Bcrypt
- SQLite (development database)
- Pipenv (dependency + virtual environment management)

---

## Project Structure (Backend)

```text
server/
├─ app.py           # Flask app, routes, config, error handlers
├─ models.py        # SQLAlchemy models (User, Note)
├─ seed.py          # Seed script for demo data
├─ migrations/      # Flask-Migrate scripts
├─ Pipfile          # Backend dependencies
└─ app.db           # Local SQLite database (ignored by git)
```

---

## Setup & Installation

From the **server** directory:

```bash
cd server

pipenv install
pipenv shell

export FLASK_APP=app
export FLASK_RUN_PORT=5555
```

For Windows PowerShell:

```powershell
$env:FLASK_APP = "app"
$env:FLASK_RUN_PORT = "5555"
```

---

## Database Migrations

```bash
flask db upgrade
```

If migrations do not exist yet:

```bash
flask db init
flask db migrate -m "create users and notes tables"
flask db upgrade
```

---

## Seeding Demo Data

```bash
python seed.py
```

Creates demo users (`alice`, `bob`, `charlie`) with `password123` and several notes each.

---

## Running the Backend

```bash
flask run
```

Runs at:

```
http://localhost:5555
```

---

## Authentication Endpoints

### POST /signup
Creates user + starts session.

### POST /login
Logs in user + starts session.

### GET /check_session
Returns the current user if logged in, else `{}`.

### DELETE /logout
Clears session.

---

## Notes Endpoints (Require Login)

### GET /notes
Supports pagination: `?page=1&per_page=10`.

### POST /notes
Creates a note.

### PATCH /notes/<id>
Updates a note owned by the current user.

### DELETE /notes/<id>
Deletes a note owned by the current user.

---

## Error Handling

Global JSON responses for:
- 404 Not Found
- 400 Bad Request
- 500 Internal Server Error

---

## Manual Testing from VS Code Terminal (Using curl + cookie file)

Instead of testing from the browser DevTools (which can run into CORS issues), you can test the backend directly from the **VS Code integrated terminal** using `curl` and a simple **cookie file** (e.g. `cookies.txt`).

### 1. Start the backend

In one terminal (inside `server/`):

```bash
pipenv shell
export FLASK_APP=app
export FLASK_RUN_PORT=5555
flask run
```

Leave this running.

---

### 2. Log in with curl and save the session cookie

Open a **second terminal** (also in `server/`), and run:

```bash
curl \
-X POST http://localhost:5555/login \
-H "Content-Type: application/json" \
-c cookies.txt \
-d '{"username": "alice", "password": "password123"}'
```

- `-c cookies.txt` tells curl to **save** any cookies (including the Flask session) into a text file named `cookies.txt`.
- The credentials here match the seeded users from `seed.py`.

#### On Windows PowerShell, instead of `\`, you will need to use backtick, for example:

 ```powershell
 curl -X POST http://localhost:5555/login `
   -H "Content-Type: application/json" `
   -c cookies.txt `
   -d '{"username": "alice", "password": "password123"}'
 ```

---

### 3. Call authenticated endpoints using the cookie file

Now that `cookies.txt` contains your session cookie, you can make authenticated requests by **sending the cookie back** with `-b cookies.txt`:

**Get notes:**

```bash
curl http://localhost:5555/notes -b cookies.txt
```

**Create a note:**

```bash
curl \
-X POST http://localhost:5555/notes \
-H "Content-Type: application/json" \
-b cookies.txt \
-d '{"title": "Test note", "content": "Created from curl"}'
```

**Update a note:**

```bash
curl -X PATCH http://localhost:5555/notes/1 \
-H "Content-Type: application/json" \
-b cookies.txt \
-d '{"content": "Updated via curl"}'
```

**Delete a note:**

```bash
curl -X DELETE http://localhost:5555/notes/1 -b cookies.txt
```

If your session expires or you want to switch users, just run the login curl again with a different username and password.

---

## Summary

- Use **Pipenv** + migrations + `seed.py` to set up the backend.
- Use **session-based auth** (`/signup`, `/login`, `/check_session`, `/logout`).
- Use **curl + cookies.txt** in the VS Code terminal to manually test authenticated routes without running into CORS issues.

