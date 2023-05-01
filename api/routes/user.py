from fastapi import APIRouter, Request, HTTPException
from ..utils.prisma import prisma

router = APIRouter(prefix="/user")


@router.get("/{user_id}")
async def get_centerline(request: Request, user_id: int):
    if user_id != request.state.user.id:
        raise HTTPException(status_code=403, detail="Cannot access other users")
    return await prisma.user.find_unique(where={"id": user_id})


@router.post("/")
async def creaste_user():
    return await prisma.user.create()
