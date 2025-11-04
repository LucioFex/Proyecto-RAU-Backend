from fastapi import APIRouter, HTTPException, status
from app.api.deps import OnboardingDep, UserIdDep
from app.schemas.onboarding import OnboardingRequest, OnboardingState

router = APIRouter()

@router.get("/onboarding", response_model=OnboardingState)
async def get_onboarding(me: UserIdDep, svc: OnboardingDep):
    if not me:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await svc.get(me)

@router.post("/onboarding", response_model=OnboardingState)
async def save_onboarding(body: OnboardingRequest, me: UserIdDep, svc: OnboardingDep):
    if not me:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return await svc.save(me, body)
