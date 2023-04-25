from fastapi import APIRouter,Depends
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

from ..utils.prisma import prisma

SECRET = "hello-there"
manager = LoginManager(SECRET, token_url="/auth/token", use_cookie=True)

router = APIRouter(prefix="/auth")

@manager.user_loader()
async def load_user(email: str):
  return await prisma.user.find_unique(where={"email":email})

@router.post("/login")
async def login(data: OAuth2PasswordRequestForm = Depends()):
  email = data.username
  password = data.password

  user = await load_user(email)
  if not user: raise InvalidCredentialsException
  if password != user.password: raise InvalidCredentialsException

  access_token = manager.create_access_token(data={"sub":email})

  return {'access_token': access_token}

@router.get("/protected")
async def protected_route(user=Depends(manager)):
  return {"user":user}