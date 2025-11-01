from app.repositories.memory.users_repo import UsersRepo
from app.repositories.memory.communities_repo import CommunitiesRepo
from app.schemas.onboarding import OnboardingRequest, OnboardingState

class OnboardingService:
    def __init__(self, users: UsersRepo, comms: CommunitiesRepo):
        self.users = users
        self.comms = comms

    def save(self, user_id: str, body: OnboardingRequest) -> OnboardingState:
        # guardar preferencias del usuario
        state = self.users.set_onboarding(user_id, {
            "careers": body.careers,
            "year": body.year,
            "graduation_year": body.graduation_year,
            "favorite_communities": body.favorite_communities,
        })
        # optional: auto-join a comunidades favoritas válidas
        for cid in body.favorite_communities:
            if cid in self.comms.data:
                self.comms.join(cid, user_id)
        return OnboardingState(**state)

    def get(self, user_id: str) -> OnboardingState:
        return OnboardingState(**self.users.get_onboarding(user_id))
