from fastapi import APIRouter, Depends, Response, Cookie, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserResponse,
)
from app.services.auth_service import register_user, login_user, refresh_tokens
from app.models.user import User
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    tokens = register_user(db, data)
    response.set_cookie(key="access_token", value=tokens.access_token, httponly=True, samesite="lax", max_age=1800)
    response.set_cookie(key="refresh_token", value=tokens.refresh_token, httponly=True, samesite="lax", max_age=604800)
    return tokens


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    tokens = login_user(db, data)
    response.set_cookie(key="access_token", value=tokens.access_token, httponly=True, samesite="lax", max_age=1800)
    response.set_cookie(key="refresh_token", value=tokens.refresh_token, httponly=True, samesite="lax", max_age=604800)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    response: Response,
    data: Optional[RefreshRequest] = None,
    refresh_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    token = refresh_token or (data.refresh_token if data else None)
    if not token:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token provided")
    tokens = refresh_tokens(db, token)
    response.set_cookie(key="access_token", value=tokens.access_token, httponly=True, samesite="lax", max_age=1800)
    response.set_cookie(key="refresh_token", value=tokens.refresh_token, httponly=True, samesite="lax", max_age=604800)
    return tokens


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}