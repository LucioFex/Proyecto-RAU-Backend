from __future__ import annotations
from typing import Optional, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.users import UserCreate, UserPublic
from app.core.security import hash_password, verify_password

class UsersRepoPG:
    """
    Repositorio de usuarios en Postgres (Neon).
    Duck-typing compatible con UsersRepo in-memory.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

    # ------- helpers -------
    @staticmethod
    def _to_public(row: Dict[str, Any]) -> UserPublic:
        return UserPublic(
            id=str(row["usuario_id"]),
            name=row["nombrecompleto"],
            username=row.get("username"),
            email=row["email"],
            role=row["rol"],
            avatar_url=row.get("avatar_url"),
            title=None,
            bio=row.get("bio"),
        )

    # ------- CRUD auth/perfil -------
    async def create(self, user: UserCreate) -> UserPublic:
        q = text("""
            INSERT INTO usuario (email, nombreCompleto, username, rol, bio, avatar_url, password_hash)
            VALUES (:email, :nombre, :username, :rol, NULL, NULL, :password_hash)
            RETURNING usuario_id, email, nombreCompleto, username, rol, bio, avatar_url
        """)
        res = await self.session.execute(q, {
            "email": user.email,
            "nombre": user.name,
            "username": user.username,
            "rol": user.role,
            "password_hash": hash_password(user.password).encode()  # passlib -> bytes
        })
        row = res.mappings().one()
        await self.session.commit()
        return self._to_public(dict(row))

    async def get_by_email(self, email: str) -> Optional[dict]:
        q = text("""
            SELECT usuario_id, email, nombreCompleto, username, rol, bio, avatar_url, password_hash
            FROM usuario WHERE email = :email
        """)
        res = await self.session.execute(q, {"email": email})
        row = res.mappings().first()
        return dict(row) if row else None

    async def get_public(self, user_id: str) -> Optional[UserPublic]:
        q = text("""
            SELECT usuario_id, email, nombreCompleto, username, rol, bio, avatar_url
            FROM usuario WHERE usuario_id = :id
        """)
        res = await self.session.execute(q, {"id": int(user_id)})
        row = res.mappings().first()
        return self._to_public(dict(row)) if row else None

    async def verify(self, email: str, password: str) -> Optional[dict]:
        rec = await self.get_by_email(email)
        if not rec:
            return None
        # BYTEA puede venir como memoryview -> convierto a bytes
        stored = rec["password_hash"]
        if isinstance(stored, memoryview):
            stored = stored.tobytes()
        ok = verify_password(password, bytes(stored))
        return rec if ok else None

    async def update(self, user_id: str, patch: dict) -> Optional[UserPublic]:
        sets = []
        params = {"id": int(user_id)}
        if (name := patch.get("name")) is not None:
            sets.append("nombreCompleto = :nombre")
            params["nombre"] = name
        if (bio := patch.get("bio")) is not None:
            sets.append("bio = :bio")
            params["bio"] = bio
        if (avatar := patch.get("avatar_url")) is not None:
            sets.append("avatar_url = :avatar")
            params["avatar"] = avatar
        if not sets:
            return await self.get_public(user_id)

        q = text(f"""
            UPDATE usuario SET {", ".join(sets)}
            WHERE usuario_id = :id
            RETURNING usuario_id, email, nombreCompleto, username, rol, bio, avatar_url
        """)
        res = await self.session.execute(q, params)
        row = res.mappings().first()
        await self.session.commit()
        return self._to_public(dict(row)) if row else None

    # ------- Onboarding / preferencias -------
    async def get_onboarding(self, user_id: str) -> dict:
        q = text("""
            SELECT carrera_nombre, cuatrimestre, on_boarded
            FROM preferencia_usuario WHERE usuario_id = :id
        """)
        res = await self.session.execute(q, {"id": int(user_id)})
        row = res.mappings().first()
        return {
            "done": bool(row["on_boarded"]) if row else False,
            "careers": [row["carrera_nombre"]] if row and row["carrera_nombre"] else [],
            "year": row["cuatrimestre"] if row else None,
            "graduation_year": None,
            "favorite_communities": []
        }

    async def set_onboarding(self, user_id: str, data: dict) -> dict:
        careers = data.get("careers") or []
        career = careers[0] if careers else None
        year = data.get("year")
        done = bool(career or data.get("favorite_communities"))
        q = text("""
            INSERT INTO preferencia_usuario (usuario_id, carrera_nombre, cuatrimestre, on_boarded)
            VALUES (:id, :carrera, :cuatri, :done)
            ON CONFLICT (usuario_id)
            DO UPDATE SET carrera_nombre = EXCLUDED.carrera_nombre,
                          cuatrimestre = EXCLUDED.cuatrimestre,
                          on_boarded = EXCLUDED.on_boarded,
                          actualizado_en = NOW()
        """)
        await self.session.execute(q, {"id": int(user_id), "carrera": career, "cuatri": year, "done": done})
        await self.session.commit()
        return {
            "done": done,
            "careers": careers,
            "year": year,
            "graduation_year": data.get("graduation_year"),
            "favorite_communities": data.get("favorite_communities") or []
        }
