from fastapi import APIRouter, HTTPException, status
from app.api.deps import CommsDep, UserIdDep
from app.schemas.communities import CommunityCreate, CommunityPublic

router = APIRouter()

@router.get("/communities", response_model=list[CommunityPublic])
def search_communities(q: str | None = None, limit: int = 20, comms: CommsDep = None):
    return comms.search(q, limit)

@router.post("/communities", response_model=CommunityPublic, status_code=201)
def create_community(body: CommunityCreate, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return comms.create(body)

@router.get("/communities/{community_id}", response_model=CommunityPublic)
def get_community(community_id: str, comms: CommsDep):
    c = comms.get(community_id)
    if not c: raise HTTPException(status_code=404, detail="No encontrado")
    return c

@router.post("/communities/{community_id}/join", status_code=204)
def join(community_id: str, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    comms.join(community_id, me)

@router.delete("/communities/{community_id}/leave", status_code=204)
def leave(community_id: str, me: UserIdDep, comms: CommsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    comms.leave(community_id, me)
