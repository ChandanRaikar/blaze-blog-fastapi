from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.auth import can_manage_post, get_current_user, login_redirect
from app.database import get_db
from app.models import Post, utcnow

router = APIRouter(tags=["posts"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Annotated[Session, Depends(get_db)]):
    user = get_current_user(request, db)
    posts = (
        db.query(Post)
        .options(joinedload(Post.author))
        .order_by(Post.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        request,
        "index.html",
        {"user": user, "posts": posts},
    )


@router.get("/posts/new", response_class=HTMLResponse)
def new_post_form(request: Request, db: Annotated[Session, Depends(get_db)]):
    user = get_current_user(request, db)
    if not user:
        return login_redirect()
    return templates.TemplateResponse(
        request,
        "post_form.html",
        {"user": user, "post": None, "error": None, "mode": "create"},
    )


@router.post("/posts/new", response_class=HTMLResponse)
def create_post(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    user = get_current_user(request, db)
    if not user:
        return login_redirect()

    title = title.strip()
    body = body.strip()
    error: Optional[str] = None
    if not title:
        error = "Title is required."
    elif not body:
        error = "Body is required."

    if error:
        return templates.TemplateResponse(
            request,
            "post_form.html",
            {
                "user": user,
                "post": Post(title=title, body=body),
                "error": error,
                "mode": "create",
            },
            status_code=400,
        )

    post = Post(title=title, body=body, author_id=user.id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return RedirectResponse(f"/posts/{post.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/posts/{post_id}", response_class=HTMLResponse)
def post_detail(
    request: Request,
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_current_user(request, db)
    post = (
        db.query(Post)
        .options(joinedload(Post.author))
        .filter(Post.id == post_id)
        .first()
    )
    if not post:
        return templates.TemplateResponse(
            request,
            "404.html",
            {"user": user},
            status_code=404,
        )
    return templates.TemplateResponse(
        request,
        "post_detail.html",
        {
            "user": user,
            "post": post,
            "can_manage": bool(user and can_manage_post(user, post)),
        },
    )


@router.get("/posts/{post_id}/edit", response_class=HTMLResponse)
def edit_post_form(
    request: Request,
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_current_user(request, db)
    if not user:
        return login_redirect()

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return templates.TemplateResponse(
            request,
            "404.html",
            {"user": user},
            status_code=404,
        )
    if not can_manage_post(user, post):
        return templates.TemplateResponse(
            request,
            "403.html",
            {"user": user},
            status_code=403,
        )

    return templates.TemplateResponse(
        request,
        "post_form.html",
        {"user": user, "post": post, "error": None, "mode": "edit"},
    )


@router.post("/posts/{post_id}/edit", response_class=HTMLResponse)
def update_post(
    request: Request,
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    title: Annotated[str, Form()],
    body: Annotated[str, Form()],
):
    user = get_current_user(request, db)
    if not user:
        return login_redirect()

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return templates.TemplateResponse(
            request,
            "404.html",
            {"user": user},
            status_code=404,
        )
    if not can_manage_post(user, post):
        return templates.TemplateResponse(
            request,
            "403.html",
            {"user": user},
            status_code=403,
        )

    title = title.strip()
    body = body.strip()
    error: Optional[str] = None
    if not title:
        error = "Title is required."
    elif not body:
        error = "Body is required."

    if error:
        post.title = title
        post.body = body
        return templates.TemplateResponse(
            request,
            "post_form.html",
            {"user": user, "post": post, "error": error, "mode": "edit"},
            status_code=400,
        )

    post.title = title
    post.body = body
    post.updated_at = utcnow()
    db.commit()
    return RedirectResponse(f"/posts/{post.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/posts/{post_id}/delete")
def delete_post(
    request: Request,
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    user = get_current_user(request, db)
    if not user:
        return login_redirect()

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return templates.TemplateResponse(
            request,
            "404.html",
            {"user": user},
            status_code=404,
        )
    if not can_manage_post(user, post):
        return templates.TemplateResponse(
            request,
            "403.html",
            {"user": user},
            status_code=403,
        )

    db.delete(post)
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
