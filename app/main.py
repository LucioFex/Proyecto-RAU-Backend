from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import auth, users, communities, posts, comments
from app.api.v1 import auth, users, communities, posts, comments, health, onboarding

app = FastAPI(title=settings.app_name)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=api_prefix, tags=["auth"])
app.include_router(users.router, prefix=api_prefix, tags=["users"])
app.include_router(communities.router, prefix=api_prefix, tags=["communities"])
app.include_router(posts.router, prefix=api_prefix, tags=["posts"])
app.include_router(comments.router, prefix=api_prefix, tags=["comments"])
app.include_router(health.router, prefix=api_prefix, tags=["health"])
app.include_router(onboarding.router, prefix=api_prefix, tags=["onboarding"])
