"""
Rutas para obtener opciones de selección en el onboarding.

Estas rutas exponen listas de carreras, años académicos y años de
graduación. El frontend las utiliza para poblar los campos de
selección durante el onboarding. En esta versión las opciones se
generan en memoria; en el futuro podrían provenir de la base de datos.
"""

from fastapi import APIRouter

from app.services.options_service import OptionsService

router = APIRouter()

_options_service = OptionsService()


@router.get("/options/careers", response_model=list[str])
def get_careers() -> list[str]:
    """
    Devuelve una lista de carreras disponibles para el onboarding.
    """
    return _options_service.get_careers()


@router.get("/options/years", response_model=list[str])
def get_years() -> list[str]:
    """
    Devuelve una lista de años académicos disponibles para el onboarding.
    """
    return _options_service.get_years()


@router.get("/options/grad-years", response_model=list[str])
def get_grad_years() -> list[str]:
    """
    Devuelve una lista de años de graduación estimados para el onboarding.
    """
    return _options_service.get_grad_years()
