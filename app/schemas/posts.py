from pydantic import BaseModel
from app.schemas.users import UserPublic
from app.schemas.common import VoteStatus

class PostPublic(BaseModel):
    id: str
    community_id: str
    title: str
    content: str
    tag: str | None = None
    author: UserPublic
    upvotes: int = 0
    downvotes: int = 0
    vote_status: VoteStatus = VoteStatus.none
    comments_count: int = 0

class PostCreate(BaseModel):
    community_id: str
    title: str
    content: str
    tag: str | None = None

class VoteRequest(BaseModel):
    status: VoteStatus
