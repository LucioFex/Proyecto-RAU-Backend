import uuid
from typing import Dict, List
from app.schemas.comments import CommentCreate, CommentPublic

class CommentsRepo:
    def __init__(self):
        self.data: Dict[str, dict] = {}   # id -> {id, post_id, author_id, content}

    def _gen_id(self) -> str:
        return str(uuid.uuid4())

    def create(self, post_id: str, author_id: str, body: CommentCreate) -> CommentPublic:
        cid = self._gen_id()
        rec = {"id": cid, "post_id": post_id, "author_id": author_id, "content": body.content}
        self.data[cid] = rec
        return CommentPublic(**rec)

    def list_for_post(self, post_id: str, limit: int = 50) -> List[CommentPublic]:
        items = [CommentPublic(**r) for r in self.data.values() if r["post_id"] == post_id]
        return items[:limit]
