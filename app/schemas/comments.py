from pydantic import BaseModel

class CommentPublic(BaseModel):
    id: str
    post_id: str
    author_id: str
    content: str

class CommentCreate(BaseModel):
    content: str
