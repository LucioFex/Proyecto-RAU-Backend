import uuid
from typing import Dict
from app.repositories.base import BaseRepo
from app.schemas.users import UserCreate, UserPublic
from app.core.security import hash_password, verify_password

class UsersRepo(BaseRepo):
    def __init__(self):
        self.data: Dict[str, dict] = {}  # id -> dict
        self.onboarding: Dict[str, dict] = {}  # user_id -> onboarding dict

    def _gen_id(self) -> str:
        return str(uuid.uuid4())

    def create(self, user: UserCreate) -> UserPublic:
        uid = self._gen_id()
        record = {
            "id": uid,
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "password_hash": hash_password(user.password),
            "avatar_url": None, "title": None, "bio": None
        }
        self.data[uid] = record
        self.onboarding[uid] = {"done": False, "careers": [], "year": None, "graduation_year": None, "favorite_communities": []}
        return UserPublic(**{k:v for k,v in record.items() if k!="password_hash"})

    def get_by_email(self, email: str) -> dict | None:
        return next((u for u in self.data.values() if u["email"] == email), None)

    def get_public(self, user_id: str) -> UserPublic | None:
        rec = self.data.get(user_id)
        return UserPublic(**{k:v for k,v in rec.items() if k!="password_hash"}) if rec else None

    def verify(self, email: str, password: str) -> dict | None:
        rec = self.get_by_email(email)
        if rec and verify_password(password, rec["password_hash"]):
            return rec
        return None

    def update(self, user_id: str, patch: dict) -> UserPublic | None:
        if user_id not in self.data: return None
        self.data[user_id].update({k:v for k,v in patch.items() if v is not None})
        rec = self.data[user_id]
        return UserPublic(**{k:v for k,v in rec.items() if k!="password_hash"})

    def get_onboarding(self, user_id: str) -> dict:
        return self.onboarding.get(user_id, {"done": False, "careers": [], "year": None, "graduation_year": None, "favorite_communities": []})

    def set_onboarding(self, user_id: str, data: dict) -> dict:
        state = self.onboarding.get(user_id) or {}
        state.update(data)
        # marcar como done si tiene al menos algo útil
        state["done"] = bool(state.get("careers") or state.get("favorite_communities"))
        self.onboarding[user_id] = state
        return state
