from pydantic import BaseModel, Field

class OnboardingRequest(BaseModel):
    careers: list[str] = Field(default_factory=list)
    year: int | None = None              # año actual de cursada
    graduation_year: int | None = None   # estimado
    favorite_communities: list[str] = Field(default_factory=list)

class OnboardingState(BaseModel):
    done: bool = False
    careers: list[str] = Field(default_factory=list)
    year: int | None = None
    graduation_year: int | None = None
    favorite_communities: list[str] = Field(default_factory=list)
