from fastapi import HTTPException, status
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.users import UserCreate, UserPublic
from app.core.security import create_access_token

class AuthService:
    def __init__(self, users):
        self.users = users

    async def login(self, body: LoginRequest) -> AuthResponse:
        rec = await self.users.verify(body.email, body.password)
        if not rec:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        token = create_access_token(str(rec["usuario_id"]))
        public = await self.users.get_public(str(rec["usuario_id"]))
        return AuthResponse(user=public, access_token=token)

    async def me(self, user_id: str) -> UserPublic:
        me = await self.users.get_public(user_id)
        if not me:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return me
