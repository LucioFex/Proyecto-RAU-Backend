from fastapi import APIRouter
from app.api.deps import AuthDep, UserIdDep
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.users import UserPublic
from fastapi import HTTPException, status

router = APIRouter()

@router.post("/auth/login", response_model=AuthResponse)
async def login(body: LoginRequest, auth: AuthDep):
    return await auth.login(body)

@router.get("/auth/me", response_model=UserPublic)
async def me(user_id: UserIdDep, auth: AuthDep):
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await auth.me(user_id)
