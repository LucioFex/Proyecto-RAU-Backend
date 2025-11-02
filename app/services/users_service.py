from app.schemas.users import UserCreate, UserUpdate, UserPublic

class UsersService:
    def __init__(self, users):
        self.users = users

    async def get(self, user_id: str) -> UserPublic | None:
        return await self.users.get_public(user_id)

    async def update(self, user_id: str, patch: UserUpdate) -> UserPublic | None:
        return await self.users.update(user_id, patch.model_dump(exclude_none=True))

    async def create(self, user: UserCreate) -> UserPublic:
        """
        Crea un nuevo usuario.

        Este método delega en el repositorio subyacente. El repositorio puede
        implementar `create` de forma síncrona (memoria) o asíncrona (Postgres);
        este wrapper se encarga de hacer await cuando sea necesario.
        """
        res = self.users.create(user)
        if hasattr(res, "__await__"):
            return await res
        return res

    async def get_by_email(self, email: str) -> dict | None:
        """
        Obtiene un usuario (dict) a partir de su email.
        """
        res = self.users.get_by_email(email)
        if hasattr(res, "__await__"):
            return await res
        return res
