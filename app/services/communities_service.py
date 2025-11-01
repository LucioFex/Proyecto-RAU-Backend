from app.repositories.memory.communities_repo import CommunitiesRepo
from app.schemas.communities import CommunityCreate, CommunityPublic

class CommunitiesService:
    def __init__(self, repo: CommunitiesRepo):
        self.repo = repo

    def create(self, body: CommunityCreate) -> CommunityPublic:
        return self.repo.create(body)

    def search(self, q: str | None, limit: int = 20) -> list[CommunityPublic]:
        return self.repo.search(q, limit)

    def join(self, community_id: str, user_id: str) -> None:
        self.repo.join(community_id, user_id)

    def leave(self, community_id: str, user_id: str) -> None:
        self.repo.leave(community_id, user_id)

    def get(self, community_id: str) -> CommunityPublic | None:
        return self.repo.get(community_id)
