from typing import Annotated
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token

# --- DB session (PG) ---
from app.db.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession

# Services
from app.services.auth_service import AuthService
from app.services.users_service import UsersService
from app.services.communities_service import CommunitiesService
from app.services.posts_service import PostsService
from app.services.onboarding_service import OnboardingService

# Repos memoria
from app.repositories.memory.users_repo import UsersRepo as UsersRepoMem
from app.repositories.memory.communities_repo import CommunitiesRepo as CommsRepoMem
from app.repositories.memory.posts_repo import PostsRepo as PostsRepoMem
from app.repositories.memory.comments_repo import CommentsRepo as CommentsRepoMem

# Repos PG (nuevos)
from app.repositories.pg.users_repo_pg import UsersRepoPG
from app.repositories.pg.communities_repo_pg import CommunitiesRepoPG

# Seed memoria (si usamos memoria)
from app.infra.seed import seed_minimal

# Repositorios PG
from app.repositories.pg.posts_repo_pg import PostsRepoPG
from app.repositories.pg.comments_repo_pg import CommentsRepoPG


security = HTTPBearer(auto_error=False)

def get_current_user_id(creds: HTTPAuthorizationCredentials | None = Depends(security)) -> str | None:
    if not creds:
        return None
    try:
        payload = decode_token(creds.credentials)
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

UserIdDep = Annotated[str | None, Depends(get_current_user_id)]

BACKEND = os.getenv("STORAGE_BACKEND", "memory").lower()

# --------- FACTORÍA DE REPOS/SERVICIOS ---------
def build_services(session: AsyncSession | None = None):
    if BACKEND == "pg":
        assert session is not None, "AsyncSession requerido para PG"
        users_repo = UsersRepoPG(session)
        comms_repo = CommunitiesRepoPG(session)
        posts_repo = PostsRepoPG(session)        # <<<< PG
        comments_repo = CommentsRepoPG(session)  # <<<< PG
        return (
            AuthService(users_repo),
            UsersService(users_repo),
            CommunitiesService(comms_repo),
            PostsService(posts_repo, comments_repo),
            OnboardingService(users_repo, comms_repo),
        )
    else:
        # memoria pura (demo)
        users_repo = UsersRepoMem()
        comms_repo = CommsRepoMem()
        posts_repo = PostsRepoMem(users_repo)
        comments_repo = CommentsRepoMem()
        seed_minimal(users_repo, comms_repo, posts_repo, comments_repo)
        return (
            AuthService(users_repo),
            UsersService(users_repo),
            CommunitiesService(comms_repo),
            PostsService(posts_repo, comments_repo),
            OnboardingService(users_repo, comms_repo),
        )

# --- Dependencias inyectables ---
def _auth_dep(session: AsyncSession = Depends(get_session)) -> AuthService:
    return build_services(session)[0] if BACKEND == "pg" else build_services()[0]

def _users_dep(session: AsyncSession = Depends(get_session)) -> UsersService:
    return build_services(session)[1] if BACKEND == "pg" else build_services()[1]

def _comms_dep(session: AsyncSession = Depends(get_session)) -> CommunitiesService:
    return build_services(session)[2] if BACKEND == "pg" else build_services()[2]

def _posts_dep(session: AsyncSession = Depends(get_session)) -> PostsService:
    return build_services(session)[3] if BACKEND == "pg" else build_services()[3]

def _onboarding_dep(session: AsyncSession = Depends(get_session)) -> OnboardingService:
    return build_services(session)[4] if BACKEND == "pg" else build_services()[4]

AuthDep = Annotated[AuthService, Depends(_auth_dep)]
UsersDep = Annotated[UsersService, Depends(_users_dep)]
CommsDep = Annotated[CommunitiesService, Depends(_comms_dep)]
PostsDep = Annotated[PostsService, Depends(_posts_dep)]
OnboardingDep = Annotated[OnboardingService, Depends(_onboarding_dep)]
