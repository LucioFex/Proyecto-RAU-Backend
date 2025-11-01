from fastapi import APIRouter, HTTPException, status
from app.api.deps import UsersDep, UserIdDep
from app.schemas.users import UserUpdate, UserPublic

router = APIRouter()

@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: str, users: UsersDep):
    user = users.get(user_id)
    if not user: raise HTTPException(status_code=404, detail="No encontrado")
    return user

@router.patch("/users/me", response_model=UserPublic)
def update_me(patch: UserUpdate, me_id: UserIdDep, users: UsersDep):
    if not me_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    upd = users.update(me_id, patch)
    if not upd: raise HTTPException(status_code=404, detail="No encontrado")
    return upd
