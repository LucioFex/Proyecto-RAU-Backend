from fastapi import APIRouter, HTTPException, status
from app.api.deps import PostsDep, UserIdDep

router = APIRouter()

@router.get("/posts")
async def list_posts(communityId: str | None = None, q: str | None = None, limit: int = 20, posts: PostsDep = None):
    return await posts.list_posts(community_id=communityId, q=q, limit=limit)

@router.post("/posts", status_code=201)
async def create_post(payload: dict, me: UserIdDep, posts: PostsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    # payload: {community_id, title, body}
    return await posts.create(community_id=payload["community_id"], author_id=me, title=payload["title"], body=payload["body"])

@router.get("/posts/{post_id}")
async def get_post(post_id: str, posts: PostsDep):
    post = await posts.get(post_id)
    if not post: raise HTTPException(status_code=404, detail="No encontrado")
    return post

@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: str, payload: dict, me: UserIdDep, posts: PostsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    value = int(payload.get("value", 0))
    if value not in (-1, 1): raise HTTPException(status_code=400, detail="value debe ser -1 o 1")
    return await posts.vote(post_id=post_id, user_id=me, value=value)

@router.post("/posts/{post_id}/bookmark")
async def toggle_bookmark(post_id: str, me: UserIdDep, posts: PostsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await posts.toggle_bookmark(post_id=post_id, user_id=me)

@router.get("/posts/{post_id}/comments")
async def list_post_comments(post_id: str, limit: int = 50, posts: PostsDep = None):
    return await posts.list_comments(post_id, limit)
