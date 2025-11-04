import uuid
from typing import Dict, List
from app.schemas.posts import PostCreate, PostPublic
from app.schemas.common import VoteStatus
from app.repositories.memory.users_repo import UsersRepo

class PostsRepo:
    def __init__(self, users_repo: UsersRepo):
        self.users_repo = users_repo
        self.posts: Dict[str, dict] = {}
        self.votes: Dict[tuple, VoteStatus] = {}
        self.comments_count: Dict[str, int] = {}

    def _gen_id(self) -> str:
        return str(uuid.uuid4())

    def create(self, author_id: str, body: PostCreate) -> PostPublic:
        pid = self._gen_id()
        rec = {
            "id": pid,
            "community_id": body.community_id,
            "title": body.title,
            "content": body.content,
            "tag": body.tag,  # etiqueta del nuevo post
            "author_id": author_id,
        }
        self.posts[pid] = rec
        self.comments_count[pid] = 0
        return self._to_public(rec, current_user_id=author_id)

    # ... (otros métodos list(), get(), vote(), etc. sin cambios) ...

    def delete(self, post_id: str) -> None:
        """
        Elimina un post de la memoria y sus votos asociados.
        """
        self.posts.pop(post_id, None)
        self.votes = {k: v for k, v in self.votes.items() if k[1] != post_id}
        self.comments_count.pop(post_id, None)

    def _to_public(self, rec: dict, current_user_id: str | None = None) -> PostPublic:
        author = self.users_repo.get_public(rec["author_id"])
        up, down = self._score(rec["id"])
        return PostPublic(
            id=rec["id"],
            community_id=rec["community_id"],
            title=rec["title"],
            content=rec["content"],
            tag=rec["tag"],
            author=author,
            upvotes=up,
            downvotes=down,
            vote_status=self._vote_status(rec["id"], current_user_id),
            comments_count=self.comments_count.get(rec["id"], 0),
        )
