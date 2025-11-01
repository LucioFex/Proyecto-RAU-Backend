from pydantic import BaseModel

class CommunityBase(BaseModel):
    name: str
    description: str | None = None

class CommunityPublic(CommunityBase):
    id: str
    member_count: int = 0

class CommunityCreate(CommunityBase):
    pass
