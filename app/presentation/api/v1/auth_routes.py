from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.application.services.auth_service import authenticate_user
from app.shared.dto.token_dto import Token


router = APIRouter(prefix='/auth', tags=['AUTH'])

@router.post('/login', response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    print(form_data)
    return await authenticate_user(form_data.username, form_data.password)