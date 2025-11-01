from fastapi import HTTPException, status
from app.repositories.memory.users_repo import UsersRepo
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, AuthResponse
from app.schemas.users import UserCreate, UserPublic

class AuthService:
    def __init__(self, users: UsersRepo):
        self.users = users
        # seed mínimo para pruebas (email y pass simples)
        if not self.users.get_by_email("prof@ucema.edu.ar"):
            self.users.create(UserCreate(
                name="Profe Demo", email="prof@ucema.edu.ar", username="prof",
                role="Profesor", password="secret123"
            ))
        if not self.users.get_by_email("est@ucema.edu.ar"):
            self.users.create(UserCreate(
                name="Estudiante Demo", email="est@ucema.edu.ar", username="estu",
                role="Estudiante", password="secret123"
            ))

    def login(self, body: LoginRequest) -> AuthResponse:
        rec = self.users.verify(body.email, body.password)
        if not rec:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")
        token = create_access_token(rec["id"])
        public = self.users.get_public(rec["id"])
        return AuthResponse(user=public, access_token=token)

    def me(self, user_id: str) -> UserPublic:
        me = self.users.get_public(user_id)
        if not me:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return me
