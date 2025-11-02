from fastapi import APIRouter, HTTPException, status
from app.api.deps import CommsDep, UserIdDep
from app.schemas.communities import CommunityCreate, CommunityPublic

router = APIRouter()

@router.get("/communities", response_model=list[CommunityPublic])
async def search_communities(q: str | None = None, limit: int = 20, comms: CommsDep = None):
    return await comms.search(q, limit)

@router.post("/communities", response_model=CommunityPublic, status_code=201)
async def create_community(body: CommunityCreate, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await comms.create(body)

@router.get("/communities/{community_id}", response_model=CommunityPublic)
async def get_community(community_id: str, comms: CommsDep):
    c = await comms.get(community_id)
    if not c: raise HTTPException(status_code=404, detail="No encontrado")
    return c

@router.post("/communities/{community_id}/join", status_code=204)
async def join(community_id: str, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    await comms.join(community_id, me)

@router.delete("/communities/{community_id}/leave", status_code=204)
async def leave(community_id: str, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    await comms.leave(community_id, me)
