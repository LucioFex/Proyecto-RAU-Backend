from __future__ import annotations
from typing import Any, Dict, Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class CommentsRepoPG:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_public(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(row["comentario_id"]),
            "post_id": str(row["post_id"]),
            "author_id": str(row["autor_id"]),
            "parent_id": str(row["comentario_padre_id"]) if row.get("comentario_padre_id") is not None else None,
            "body": row["cuerpo"],
            "created_at": row["creado_en"],
            "updated_at": row["actualizado_en"],
            "upvotes": int(row.get("upvotes", 0)),
            "downvotes": int(row.get("downvotes", 0)),
            "score": int(row.get("score", 0)),
        }

    async def list_for_post(self, post_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        sql = """
        SELECT
          c.comentario_id, c.post_id, c.autor_id, c.comentario_padre_id, c.cuerpo,
          c.creado_en, c.actualizado_en,
          COALESCE(SUM(CASE WHEN cv.valor = 1 THEN 1 ELSE 0 END),0)::int AS upvotes,
          COALESCE(SUM(CASE WHEN cv.valor = -1 THEN 1 ELSE 0 END),0)::int AS downvotes,
          COALESCE(SUM(CASE WHEN cv.valor = 1 THEN 1 WHEN cv.valor = -1 THEN -1 ELSE 0 END),0)::int AS score
        FROM comentario c
        LEFT JOIN comentario_voto cv ON cv.comentario_id = c.comentario_id
        WHERE c.post_id = :pid
        GROUP BY c.comentario_id
        ORDER BY c.creado_en ASC
        LIMIT :lim
        """
        res = await self.session.execute(text(sql), {"pid": int(post_id), "lim": limit})
        return [self._to_public(dict(r)) for r in res.mappings().all()]

    async def create(self, *, post_id: str, author_id: str, body: str, parent_id: Optional[str]) -> Dict[str, Any]:
        sql = """
        INSERT INTO comentario (post_id, autor_id, comentario_padre_id, cuerpo)
        VALUES (:pid, :uid, :parent, :body)
        RETURNING comentario_id, post_id, autor_id, comentario_padre_id, cuerpo, creado_en, actualizado_en
        """
        res = await self.session.execute(text(sql), {
            "pid": int(post_id), "uid": int(author_id),
            "parent": int(parent_id) if parent_id else None,
            "body": body
        })
        row = dict(res.mappings().one())
        await self.session.commit()
        row.update({"upvotes": 0, "downvotes": 0, "score": 0})
        return self._to_public(row)

    async def vote(self, *, comment_id: str, user_id: str, value: int) -> Dict[str, Any]:
        upsert = """
        INSERT INTO comentario_voto (comentario_id, usuario_id, valor)
        VALUES (:cid, :uid, :val)
        ON CONFLICT (comentario_id, usuario_id) DO UPDATE SET valor = EXCLUDED.valor, votado_en = NOW()
        """
        await self.session.execute(text(upsert), {"cid": int(comment_id), "uid": int(user_id), "val": int(value)})
        await self.session.commit()
        sql = """
        SELECT
          c.comentario_id, c.post_id, c.autor_id, c.comentario_padre_id, c.cuerpo,
          c.creado_en, c.actualizado_en,
          COALESCE(SUM(CASE WHEN cv.valor = 1 THEN 1 ELSE 0 END),0)::int AS upvotes,
          COALESCE(SUM(CASE WHEN cv.valor = -1 THEN 1 ELSE 0 END),0)::int AS downvotes,
          COALESCE(SUM(CASE WHEN cv.valor = 1 THEN 1 WHEN cv.valor = -1 THEN -1 ELSE 0 END),0)::int AS score
        FROM comentario c
        LEFT JOIN comentario_voto cv ON cv.comentario_id = c.comentario_id
        WHERE c.comentario_id = :cid
        GROUP BY c.comentario_id
        """
        res = await self.session.execute(text(sql), {"cid": int(comment_id)})
        return self._to_public(dict(res.mappings().one()))
