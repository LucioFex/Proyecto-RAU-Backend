from fastapi import APIRouter, Depends
from app.api.deps import AuthDep, UserIdDep
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.users import UserPublic

router = APIRouter()

@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest, auth: AuthDep):
    return auth.login(body)

@router.get("/auth/me", response_model=UserPublic)
def me(user_id: UserIdDep, auth: AuthDep):
    # /auth/me requiere token válido
    if not user_id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return auth.me(user_id)
