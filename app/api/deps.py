from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token
from app.repositories.memory.users_repo import UsersRepo
from app.repositories.memory.communities_repo import CommunitiesRepo
from app.repositories.memory.posts_repo import PostsRepo
from app.repositories.memory.comments_repo import CommentsRepo
from app.services.auth_service import AuthService
from app.services.users_service import UsersService
from app.services.communities_service import CommunitiesService
from app.services.posts_service import PostsService

# repos singletons en memoria para esta demo
_users = UsersRepo()
_comms = CommunitiesRepo()
_posts = PostsRepo(_users)
_comments = CommentsRepo()

# services
auth_service = AuthService(_users)
users_service = UsersService(_users)
communities_service = CommunitiesService(_comms)
posts_service = PostsService(_posts, _comments)

security = HTTPBearer(auto_error=False)

def get_current_user_id(creds: HTTPAuthorizationCredentials | None = Depends(security)) -> str | None:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

AuthDep = Annotated[AuthService, Depends(lambda: auth_service)]
UsersDep = Annotated[UsersService, Depends(lambda: users_service)]
CommsDep = Annotated[CommunitiesService, Depends(lambda: communities_service)]
PostsDep = Annotated[PostsService, Depends(lambda: posts_service)]
UserIdDep = Annotated[str | None, Depends(get_current_user_id)]
