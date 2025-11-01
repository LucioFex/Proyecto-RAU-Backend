from app.repositories.memory.posts_repo import PostsRepo
from app.repositories.memory.comments_repo import CommentsRepo
from app.schemas.posts import PostCreate, PostPublic, VoteRequest
from app.schemas.comments import CommentCreate, CommentPublic

class PostsService:
    def __init__(self, posts: PostsRepo, comments: CommentsRepo):
        self.posts = posts
        self.comments = comments

    def list(self, community_id: str | None, q: str | None, limit: int = 20) -> list[PostPublic]:
        return self.posts.list(community_id=community_id, q=q, limit=limit)

    def create(self, author_id: str, body: PostCreate) -> PostPublic:
        return self.posts.create(author_id, body)

    def get(self, post_id: str, user_id: str | None) -> PostPublic | None:
        return self.posts.get(post_id, user_id)

    def vote(self, user_id: str, post_id: str, body: VoteRequest) -> PostPublic | None:
        return self.posts.vote(user_id, post_id, body.status)

    def list_comments(self, post_id: str, limit: int = 50) -> list[CommentPublic]:
        return self.comments.list_for_post(post_id, limit)

    def add_comment(self, post_id: str, author_id: str, body: CommentCreate) -> CommentPublic:
        c = self.comments.create(post_id, author_id, body)
        self.posts.inc_comments(post_id)
        return c
