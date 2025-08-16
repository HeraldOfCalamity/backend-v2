

from app.core.exceptions import raise_unauthorized
from app.core.security import create_access_token, verify_password
from app.infrastructure.schemas.role import Role
from app.infrastructure.schemas.user import User
from app.shared.dto.token_dto import Token


async def authenticate_user(email: str, password: str) -> Token:
    user = await User.find_one(User.email == email, User.isActive == True)
    if not user: 
        raise raise_unauthorized('Credenciales Invalidas')
    
    role = await Role.get(user.role)
    if not role:
        raise raise_unauthorized('Rol no encontrado.')

    if verify_password(password, user.password):
        payload = {
            'user_id': str(user.id),
            'name': user.name,
            'lastname': user.lastname,
            'isVerified': user.isVerified,
            'tenant_id': str(user.tenant_id),
            'role': role.name,

        }

        access_token = create_access_token(data=payload)
        return Token(access_token=access_token)
    
    raise raise_unauthorized('Credenciales Invalidas.')