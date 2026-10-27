import os
import secrets

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine
from app.routers import auth_routes, posts

Base.metadata.create_all(bind=engine, checkfirst=True)

app = FastAPI(title="Blazing Blog", description="A FastAPI micro blog")

secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="blog_session",
    max_age=60 * 60 * 24 * 14,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_routes.router)
app.include_router(posts.router)
