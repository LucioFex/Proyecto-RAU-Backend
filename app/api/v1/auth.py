from fastapi import APIRouter
from app.api.deps import AuthDep, UserIdDep
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.users import UserPublic
from fastapi import HTTPException, status

from pydantic import BaseModel, EmailStr
from app.api.deps import UsersDep
from app.schemas.users import UserCreate, UserPublic
from app.schemas.common import Role

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nombreCompleto: str
    rol: Role


@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest, auth: AuthDep):
    return await auth.login(body)

@router.get("/auth/me", response_model=UserPublic)
async def me(user_id: UserIdDep, auth: AuthDep):
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await auth.me(user_id)


@router.post("/auth/register", response_model=UserPublic, status_code=201)
async def register(body: RegisterRequest, users: UsersDep):
    existing = await users.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado",
        )
    username = body.email.split("@")[0]
    user_create = UserCreate(
        name=body.nombreCompleto,
        email=body.email,
        username=username,
        role=body.rol,
        password=body.password,
    )
    new_user = await users.create(user_create)
    return new_user