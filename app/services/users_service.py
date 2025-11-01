from app.repositories.memory.users_repo import UsersRepo
from app.schemas.users import UserUpdate, UserPublic

class UsersService:
    def __init__(self, users: UsersRepo):
        self.users = users

    def get(self, user_id: str) -> UserPublic | None:
        return self.users.get_public(user_id)

    def update(self, user_id: str, patch: UserUpdate) -> UserPublic | None:
        return self.users.update(user_id, patch.model_dump(exclude_none=True))
