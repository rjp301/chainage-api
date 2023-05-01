from fastapi import APIRouter, Request, HTTPException, Response
from ..utils.prisma import prisma

router = APIRouter(prefix="/user")


@router.get("/{user_id}")
async def get_centerline(request: Request, user_id: int):
    if user_id != request.state.user.id:
        raise HTTPException(status_code=403, detail="Cannot access other users")
    return await prisma.user.find_unique(where={"id": user_id})


@router.post("/")
async def create_user(response: Response, full_name="", email=""):
    return await prisma.user.create(data={"full_name": full_name, "email": email})
