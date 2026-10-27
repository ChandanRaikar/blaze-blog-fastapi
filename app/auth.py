from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return get_user_by_id(db, user_id)


def require_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = get_current_user(request, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return user


def login_redirect() -> RedirectResponse:
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


def can_manage_post(user: User, post) -> bool:
    """Author or admin may edit/delete a post."""
    return user.is_admin or post.author_id == user.id
