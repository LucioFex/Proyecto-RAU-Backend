import uuid
from typing import Dict, List
from app.schemas.posts import PostCreate, PostPublic
from app.schemas.common import VoteStatus
from app.repositories.memory.users_repo import UsersRepo

class PostsRepo:
    def __init__(self, users_repo: UsersRepo):
        self.users_repo = users_repo
        self.posts: Dict[str, dict] = {}        # id -> post dict
        self.votes: Dict[tuple, VoteStatus] = {}  # (user_id, post_id) -> status
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
            "tag": body.tag,
            "author_id": author_id
        }
        self.posts[pid] = rec
        self.comments_count[pid] = 0
        return self._to_public(rec, current_user_id=author_id)

    def list(self, *, community_id: str | None = None, q: str | None = None, limit: int = 20) -> List[PostPublic]:
        items = []
        for rec in self.posts.values():
            if community_id and rec["community_id"] != community_id:
                continue
            if q and q.lower() not in (rec["title"] + " " + rec["content"]).lower():
                continue
            items.append(rec)
        items = items[:limit]
        return [self._to_public(r) for r in items]

    def get(self, post_id: str, current_user_id: str | None = None) -> PostPublic | None:
        rec = self.posts.get(post_id)
        return self._to_public(rec, current_user_id) if rec else None

    def vote(self, user_id: str, post_id: str, status: VoteStatus) -> PostPublic | None:
        if post_id not in self.posts: return None
        key = (user_id, post_id)
        self.votes[key] = status
        return self._to_public(self.posts[post_id], user_id)

    def inc_comments(self, post_id: str) -> None:
        self.comments_count[post_id] = self.comments_count.get(post_id, 0) + 1

    # helpers
    def _score(self, post_id: str) -> tuple[int, int]:
        ups = sum(1 for (u,p), s in self.votes.items() if p == post_id and s == VoteStatus.up)
        downs = sum(1 for (u,p), s in self.votes.items() if p == post_id and s == VoteStatus.down)
        return ups, downs

    def _vote_status(self, post_id: str, user_id: str | None) -> VoteStatus:
        if not user_id: return VoteStatus.none
        return self.votes.get((user_id, post_id), VoteStatus.none)

    def _to_public(self, rec: dict, current_user_id: str | None = None) -> PostPublic:
        author = self.users_repo.get_public(rec["author_id"])
        up, down = self._score(rec["id"])
        return PostPublic(
            id=rec["id"], community_id=rec["community_id"], title=rec["title"],
            content=rec["content"], tag=rec["tag"], author=author,
            upvotes=up, downvotes=down, vote_status=self._vote_status(rec["id"], current_user_id),
            comments_count=self.comments_count.get(rec["id"], 0)
        )
