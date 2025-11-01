from fastapi import APIRouter, HTTPException, status
from app.api.deps import PostsDep, UserIdDep
from app.schemas.posts import PostPublic, PostCreate, VoteRequest

router = APIRouter()

@router.get("/posts", response_model=list[PostPublic])
def list_posts(communityId: str | None = None, q: str | None = None, limit: int = 20, posts: PostsDep = None):
    return posts.list(community_id=communityId, q=q, limit=limit)

@router.post("/posts", response_model=PostPublic, status_code=201)
def create_post(body: PostCreate, me: UserIdDep, posts: PostsDep):
    if not me:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return posts.create(me, body)

@router.get("/posts/{post_id}", response_model=PostPublic)
def get_post(post_id: str, me: UserIdDep, posts: PostsDep):
    p = posts.get(post_id, me)
    if not p: raise HTTPException(status_code=404, detail="No encontrado")
    return p

@router.post("/posts/{post_id}/vote", response_model=PostPublic)
def vote_post(post_id: str, body: VoteRequest, me: UserIdDep, posts: PostsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    p = posts.vote(me, post_id, body)
    if not p: raise HTTPException(status_code=404, detail="No encontrado")
    return p
