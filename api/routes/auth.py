from fastapi import APIRouter,Depends
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordRequestForm

from fastapi_login import LoginManager
from fastapi_login.exceptions import InvalidCredentialsException

from ..utils.prisma import prisma

import bcrypt

SECRET = "hello-there"
manager = LoginManager(secret=SECRET, token_url="/auth/login", use_cookie=True)

router = APIRouter(prefix="/auth")

@manager.user_loader()
async def load_user(email: str):
  return await prisma.user.find_unique(where={"email":email})

@router.post("/signup")
async def signup(data: OAuth2PasswordRequestForm = Depends()):
  return await prisma.user.create(data={
    "email":data.username,
    "hashed_password":data.password,
  })

@router.post("/login")
async def login(data: OAuth2PasswordRequestForm = Depends()):
  email = data.username
  password = data.password

  user = await load_user(email)
  if not user: raise InvalidCredentialsException
  if password != user.hashed_password: raise InvalidCredentialsException

  access_token = manager.create_access_token(data={"sub":email})
  response = Response()
  manager.set_cookie(response,access_token)

  return response

@router.post("/logout")
async def logout():
  response = Response()
  response.delete_cookie("access-token")
  return response

@router.get("/protected")
async def protected_route(user=Depends(manager)):
  return {"user":user}