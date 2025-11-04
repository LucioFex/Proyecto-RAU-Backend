from __future__ import annotations

from app.schemas.onboarding import OnboardingRequest, OnboardingState


class OnboardingService:
    """
    Servicio de onboarding que guarda y recupera las preferencias del usuario.
    Soporta tanto repositorios síncronos (memoria) como asíncronos (PostgreSQL).
    """

    def __init__(self, users, comms):
        self.users = users
        self.comms = comms

    async def save(self, user_id: str, body: OnboardingRequest) -> OnboardingState:
        """
        Guarda las preferencias de onboarding para el usuario y devuelve el estado actualizado.
        Si el repositorio devuelve una corutina, la espera antes de continuar.
        """
        payload = {
            "careers": body.careers,
            "year": body.year,
            "graduation_year": body.graduation_year,
            "favorite_communities": body.favorite_communities,
        }

        # Llama a set_onboarding; puede ser síncrono o asíncrono
        res = self.users.set_onboarding(user_id, payload)
        state = await res if hasattr(res, "__await__") else res

        # Auto-unirse a comunidades favoritas si el repo tiene join
        for cid in body.favorite_communities:
            join_res = self.comms.join(cid, user_id)
            if hasattr(join_res, "__await__"):
                await join_res

        return OnboardingState(**state)

    async def get(self, user_id: str) -> OnboardingState:
        """
        Recupera el estado de onboarding del usuario.
        Soporta repositorios síncronos o asíncronos.
        """
        res = self.users.get_onboarding(user_id)
        state = await res if hasattr(res, "__await__") else res
        return OnboardingState(**state)
