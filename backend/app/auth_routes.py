"""Authentication routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(email: str, password: str):
    """Login endpoint placeholder."""
    return {"status": "success", "message": "Authentication not implemented"}


@router.post("/logout")
async def logout():
    """Logout endpoint placeholder."""
    return {"status": "success", "message": "Logout successful"}
