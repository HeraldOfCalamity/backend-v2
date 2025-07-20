import logging
from fastapi.requests import Request
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
logger = logging.getLogger('uvicorn.error')

def raise_duplicate_entity(entity: str):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f'{entity} ya existe en la aplicacion.'
    )

def raise_not_found(entity: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f'{entity} no encontrado.'
    )

def raise_unauthorized(message: str = 'No autorizado.'):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message
    )

def raise_forbidden(message: str = 'Acceso denegado.'):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message
    )

def raise_internal_error(message: str = 'Error interno del servidor.'):
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=message
    )

async def internal_errror_handler(request: Request, exc: Exception):
    logger.error(f'Error inesperado en {request.url}: {exc}')
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': 'Error interno del servidor.'}
    )
