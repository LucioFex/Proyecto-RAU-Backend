import uuid
from typing import Dict, List
from app.schemas.communities import CommunityCreate, CommunityPublic

class CommunitiesRepo:
    def __init__(self):
        self.data: Dict[str, dict] = {}           # id -> {id,name,description}
        self.members: Dict[str, set] = {}         # community_id -> {user_ids}

    def _gen_id(self) -> str:
        return str(uuid.uuid4())

    def create(self, body: CommunityCreate) -> CommunityPublic:
        cid = self._gen_id()
        self.data[cid] = {"id": cid, "name": body.name, "description": body.description}
        self.members[cid] = set()
        return CommunityPublic(id=cid, name=body.name, description=body.description, member_count=0)

    def join(self, community_id: str, user_id: str) -> None:
        self.members.setdefault(community_id, set()).add(user_id)

    def leave(self, community_id: str, user_id: str) -> None:
        self.members.setdefault(community_id, set()).discard(user_id)

    def get(self, community_id: str) -> CommunityPublic | None:
        c = self.data.get(community_id)
        if not c: return None
        mc = len(self.members.get(community_id, set()))
        return CommunityPublic(**c, member_count=mc)

    def search(self, q: str | None, limit: int = 20) -> List[CommunityPublic]:
        out = []
        for c in self.data.values():
            if q and q.lower() not in c["name"].lower():
                continue
            out.append(self.get(c["id"]))
            if len(out) >= limit: break
        return out
