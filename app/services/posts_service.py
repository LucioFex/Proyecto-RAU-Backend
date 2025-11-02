from __future__ import annotations
from typing import Optional, List, Dict, Any

class PostsService:
    def __init__(self, posts_repo, comments_repo):
        self.posts = posts_repo
        self.comments = comments_repo

    async def list_posts(self, community_id: Optional[str], q: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
        return await self.posts.list(community_id=community_id, q=q, limit=limit)

    async def create(self, *, community_id: str, author_id: str, title: str, body: str) -> Dict[str, Any]:
        return await self.posts.create(community_id=community_id, author_id=author_id, title=title, body=body)

    async def get(self, post_id: str) -> Optional[Dict[str, Any]]:
        return await self.posts.get(post_id)

    async def vote(self, *, post_id: str, user_id: str, value: int) -> Dict[str, Any]:
        return await self.posts.vote(post_id=post_id, user_id=user_id, value=value)

    async def toggle_bookmark(self, *, post_id: str, user_id: str) -> Dict[str, Any]:
        return await self.posts.toggle_bookmark(post_id=post_id, user_id=user_id)

    async def list_comments(self, post_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.comments.list_for_post(post_id, limit)
