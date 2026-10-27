from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_user,
    get_current_user,
    get_user_by_username,
    hash_password,
)
from app.database import get_db
from app.models import User

router = APIRouter(tags=["auth"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/register", response_class=HTMLResponse)
def register_form(request: Request, db: Annotated[Session, Depends(get_db)]):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"user": None, "error": None},
    )


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    username: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    password_confirm: Annotated[str, Form()],
):
    error: Optional[str] = None
    username = username.strip()
    email = email.strip().lower()

    if len(username) < 3 or len(username) > 50:
        error = "Username must be 3–50 characters."
    elif len(password) < 6:
        error = "Password must be at least 6 characters."
    elif password != password_confirm:
        error = "Passwords do not match."
    elif get_user_by_username(db, username):
        error = "That username is already taken."
    elif db.query(User).filter(User.email == email).first():
        error = "That email is already registered."

    if error:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"user": None, "error": error},
            status_code=400,
        )

    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    request.session["user_id"] = new_user.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request, db: Annotated[Session, Depends(get_db)]):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"user": None, "error": None},
    )


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    user = authenticate_user(db, username.strip(), password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"user": None, "error": "Invalid username or password."},
            status_code=401,
        )
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
