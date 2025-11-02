from __future__ import annotations
from typing import List, Optional, Dict, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.communities import CommunityCreate, CommunityPublic

class CommunitiesRepoPG:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_public(row: Dict[str, Any]) -> CommunityPublic:
        return CommunityPublic(
            id=str(row["comunidad_id"]),
            name=row["nombre"],
            description=row.get("descripcion"),
            member_count=row.get("member_count", 0)
        )

    async def create(self, body: CommunityCreate) -> CommunityPublic:
        q = text("""
            INSERT INTO comunidad (nombre, descripcion, es_oficial)
            VALUES (:nombre, :desc, false)
            RETURNING comunidad_id, nombre, descripcion
        """)
        res = await self.session.execute(q, {"nombre": body.name, "desc": body.description})
        row = res.mappings().one()
        await self.session.commit()
        row = dict(row)
        row["member_count"] = 0
        return self._to_public(row)

    async def join(self, community_id: str, user_id: str) -> None:
        q = text("""
            INSERT INTO comunidad_miembro (comunidad_id, usuario_id, rol)
            VALUES (:cid, :uid, 'U')
            ON CONFLICT (comunidad_id, usuario_id) DO NOTHING
        """)
        await self.session.execute(q, {"cid": int(community_id), "uid": int(user_id)})
        await self.session.commit()

    async def leave(self, community_id: str, user_id: str) -> None:
        q = text("""
            DELETE FROM comunidad_miembro
            WHERE comunidad_id = :cid AND usuario_id = :uid
        """)
        await self.session.execute(q, {"cid": int(community_id), "uid": int(user_id)})
        await self.session.commit()

    async def get(self, community_id: str) -> Optional[CommunityPublic]:
        q = text("""
            SELECT c.comunidad_id, c.nombre, c.descripcion,
                   COUNT(m.usuario_id)::int AS member_count
            FROM comunidad c
            LEFT JOIN comunidad_miembro m ON m.comunidad_id = c.comunidad_id
            WHERE c.comunidad_id = :cid
            GROUP BY c.comunidad_id, c.nombre, c.descripcion
        """)
        res = await self.session.execute(q, {"cid": int(community_id)})
        row = res.mappings().first()
        return self._to_public(row) if row else None

    async def search(self, qtext: str | None, limit: int = 20) -> List[CommunityPublic]:
        if qtext:
            q = text("""
                SELECT c.comunidad_id, c.nombre, c.descripcion,
                       COUNT(m.usuario_id)::int AS member_count
                FROM comunidad c
                LEFT JOIN comunidad_miembro m ON m.comunidad_id = c.comunidad_id
                WHERE c.nombre ILIKE '%' || :q || '%'
                GROUP BY c.comunidad_id, c.nombre, c.descripcion
                ORDER BY member_count DESC, c.nombre
                LIMIT :lim
            """)
            params = {"q": qtext, "lim": limit}
        else:
            q = text("""
                SELECT c.comunidad_id, c.nombre, c.descripcion,
                       COUNT(m.usuario_id)::int AS member_count
                FROM comunidad c
                LEFT JOIN comunidad_miembro m ON m.comunidad_id = c.comunidad_id
                GROUP BY c.comunidad_id, c.nombre, c.descripcion
                ORDER BY member_count DESC, c.nombre
                LIMIT :lim
            """)
            params = {"lim": limit}

        res = await self.session.execute(q, params)
        rows = res.mappings().all()
        return [self._to_public(r) for r in rows]
