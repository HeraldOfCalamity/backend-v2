from datetime import timedelta
from typing import Any, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from app.core.config import settings
from jose import JWTError, jwt

from app.core.exceptions import raise_forbidden
from app.infrastructure.schemas.permission import Permission
from app.infrastructure.schemas.role import Role
from app.infrastructure.schemas.user import User
from app.shared.dto.token_dto import TokenData
from app.shared.utils import get_utc_now

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = get_utc_now() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Token invalido o expirado',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get('user_id')
        if user_id is None:
            raise credentials_error
        
        token_data = TokenData(**payload)
    except (JWTError, ValueError):
        raise credentials_error
    
    user = await User.get(token_data.user_id)
    if user is None or not user.isActive:
        raise credentials_error
    
    return user

def require_permission(permission_name: str):
    async def permission_dependency(user: User = Depends(get_current_user)):
        role = await Role.get(user.role)
        if not role:
            raise raise_forbidden('Rol no valido')
        
        permissions = await Permission.find(
            {'_id': {'$in': role.permissions}, 'tenant_id': user.tenant_id}
        ).to_list()

        has_permission = any(p.name == permission_name for p in permissions)
        if not has_permission:
            raise raise_forbidden(f'No se tiene el permiso: {permission_name}')
        
        return user
    
    return permission_dependency

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e

