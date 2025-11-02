from __future__ import annotations
from typing import Any, Dict, Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class PostsRepoPG:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_public(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(row["post_id"]),
            "community_id": str(row["comunidad_id"]),
            "author_id": str(row["autor_id"]),
            "title": row["titulo"],
            "body": row["cuerpo"],
            "best_comment_id": str(row["mejor_comentario_id"]) if row.get("mejor_comentario_id") is not None else None,
            "created_at": row["creado_en"],
            "updated_at": row["actualizado_en"],
            "status": row["estado"],
            "upvotes": int(row.get("upvotes", 0)),
            "downvotes": int(row.get("downvotes", 0)),
            "score": int(row.get("score", 0)),
            "comments_count": int(row.get("comments_count", 0)),
        }

    async def list(self, community_id: Optional[str], q: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
        where = ["p.estado = 'A'"]
        params: Dict[str, Any] = {"lim": limit}
        if community_id:
            where.append("p.comunidad_id = :cid")
            params["cid"] = int(community_id)
        if q:
            where.append("(p.titulo ILIKE '%' || :q || '%' OR p.cuerpo ILIKE '%' || :q || '%')")
            params["q"] = q
        sql = f"""
        SELECT
          p.post_id, p.comunidad_id, p.autor_id, p.titulo, p.cuerpo, p.mejor_comentario_id,
          p.creado_en, p.actualizado_en, p.estado,
          COALESCE(SUM(CASE WHEN pv.valor = 1 THEN 1 ELSE 0 END),0)::int AS upvotes,
          COALESCE(SUM(CASE WHEN pv.valor = -1 THEN 1 ELSE 0 END),0)::int AS downvotes,
          COALESCE(SUM(CASE WHEN pv.valor = 1 THEN 1 WHEN pv.valor = -1 THEN -1 ELSE 0 END),0)::int AS score,
          COALESCE(COUNT(DISTINCT c.comentario_id),0)::int AS comments_count
        FROM post p
        LEFT JOIN post_voto pv ON pv.post_id = p.post_id
        LEFT JOIN comentario c  ON c.post_id  = p.post_id
        WHERE {" AND ".join(where)}
        GROUP BY p.post_id
        ORDER BY p.creado_en DESC
        LIMIT :lim
        """
        res = await self.session.execute(text(sql), params)
        return [self._to_public(dict(r)) for r in res.mappings().all()]

    async def get(self, post_id: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT
          p.post_id, p.comunidad_id, p.autor_id, p.titulo, p.cuerpo, p.mejor_comentario_id,
          p.creado_en, p.actualizado_en, p.estado,
          COALESCE(SUM(CASE WHEN pv.valor = 1 THEN 1 ELSE 0 END),0)::int AS upvotes,
          COALESCE(SUM(CASE WHEN pv.valor = -1 THEN 1 ELSE 0 END),0)::int AS downvotes,
          COALESCE(SUM(CASE WHEN pv.valor = 1 THEN 1 WHEN pv.valor = -1 THEN -1 ELSE 0 END),0)::int AS score,
          COALESCE(COUNT(DISTINCT c.comentario_id),0)::int AS comments_count
        FROM post p
        LEFT JOIN post_voto pv ON pv.post_id = p.post_id
        LEFT JOIN comentario c  ON c.post_id  = p.post_id
        WHERE p.post_id = :id
        GROUP BY p.post_id
        """
        res = await self.session.execute(text(sql), {"id": int(post_id)})
        row = res.mappings().first()
        return self._to_public(dict(row)) if row else None

    async def create(self, *, community_id: str, author_id: str, title: str, body: str) -> Dict[str, Any]:
        sql = """
        INSERT INTO post (comunidad_id, autor_id, titulo, cuerpo)
        VALUES (:cid, :uid, :title, :body)
        RETURNING post_id, comunidad_id, autor_id, titulo, cuerpo, mejor_comentario_id,
                  creado_en, actualizado_en, estado
        """
        res = await self.session.execute(text(sql), {
            "cid": int(community_id), "uid": int(author_id),
            "title": title, "body": body
        })
        row = dict(res.mappings().one())
        await self.session.commit()
        row.update({"upvotes": 0, "downvotes": 0, "score": 0, "comments_count": 0})
        return self._to_public(row)

    async def vote(self, *, post_id: str, user_id: str, value: int) -> Dict[str, Any]:
        upsert = """
        INSERT INTO post_voto (post_id, usuario_id, valor)
        VALUES (:pid, :uid, :val)
        ON CONFLICT (post_id, usuario_id) DO UPDATE SET valor = EXCLUDED.valor, votado_en = NOW()
        """
        await self.session.execute(text(upsert), {"pid": int(post_id), "uid": int(user_id), "val": int(value)})
        await self.session.commit()
        return await self.get(post_id)

    async def toggle_bookmark(self, *, post_id: str, user_id: str) -> Dict[str, Any]:
        exists = await self.session.execute(
            text("SELECT 1 FROM post_guardado WHERE post_id=:pid AND usuario_id=:uid"),
            {"pid": int(post_id), "uid": int(user_id)}
        )
        if exists.first():
            await self.session.execute(
                text("DELETE FROM post_guardado WHERE post_id=:pid AND usuario_id=:uid"),
                {"pid": int(post_id), "uid": int(user_id)}
            )
            action = "removed"
        else:
            await self.session.execute(
                text("INSERT INTO post_guardado (post_id, usuario_id) VALUES (:pid,:uid)"),
                {"pid": int(post_id), "uid": int(user_id)}
            )
            action = "added"
        await self.session.commit()
        return {"status": "ok", "action": action}
