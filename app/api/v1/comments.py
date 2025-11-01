from fastapi import APIRouter, HTTPException, status
from app.api.deps import PostsDep, UserIdDep
from app.schemas.comments import CommentCreate
from app.schemas.posts import PostPublic

router = APIRouter()

@router.get("/posts/{post_id}/comments")
def list_comments(post_id: str, limit: int = 50, posts: PostsDep = None):
    return {"items": posts.list_comments(post_id, limit)}

@router.post("/posts/{post_id}/comments", status_code=201)
def add_comment(post_id: str, body: CommentCreate, me: UserIdDep, posts: PostsDep):
    if not me: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    p = posts.get(post_id, me)
    if not p: raise HTTPException(status_code=404, detail="Post no encontrado")
    c = posts.add_comment(post_id, me, body)
    # Devolvemos comentario y post resumido (opcional)
    updated: PostPublic = posts.get(post_id, me)
    return {"comment": c, "post": updated}
