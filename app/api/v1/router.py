from fastapi import APIRouter

from .routers import auth, users, wishes

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(wishes.router)
