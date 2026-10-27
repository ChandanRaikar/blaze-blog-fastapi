# Blazing Blog

A FastAPI micro blog with SQLite, Tailwind CSS, session authentication, and ownership-based authorization.

## Features

- Register, log in, and log out (signed session cookies)
- Create, read, update, and delete posts
- Only the post author (or an admin) can edit or delete a post
- Server-rendered Jinja2 templates styled with Tailwind CSS

## Setup

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Optional: set a stable session secret (otherwise a random key is generated each run):

```bash
# Windows PowerShell
$env:SECRET_KEY="change-me-to-a-long-random-string"

# macOS / Linux
export SECRET_KEY="change-me-to-a-long-random-string"
```

## Run

From the project root:

```bash
uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

SQLite creates `blog.db` in the project root on first launch.

## Authorization

| Action | Who |
|--------|-----|
| View posts | Anyone |
| Create posts | Authenticated users |
| Edit / delete a post | Post author or `is_admin` user |

To promote a user to admin, set `is_admin = 1` for that row in the `users` table.
