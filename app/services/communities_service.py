from app.schemas.communities import CommunityCreate, CommunityPublic

class CommunitiesService:
    def __init__(self, repo):
        self.repo = repo

    async def create(self, body: CommunityCreate) -> CommunityPublic:
        return await self.repo.create(body)

    async def search(self, q: str | None, limit: int = 20) -> list[CommunityPublic]:
        return await self.repo.search(q, limit)

    async def join(self, community_id: str, user_id: str) -> None:
        await self.repo.join(community_id, user_id)

    async def leave(self, community_id: str, user_id: str) -> None:
        await self.repo.leave(community_id, user_id)

    async def get(self, community_id: str) -> CommunityPublic | None:
        return await self.repo.get(community_id)
