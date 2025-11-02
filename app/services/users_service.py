from app.schemas.users import UserUpdate, UserPublic

class UsersService:
    def __init__(self, users):
        self.users = users

    async def get(self, user_id: str) -> UserPublic | None:
        return await self.users.get_public(user_id)

    async def update(self, user_id: str, patch: UserUpdate) -> UserPublic | None:
        return await self.users.update(user_id, patch.model_dump(exclude_none=True))
