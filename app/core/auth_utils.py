from fastapi import Depends
from app.core.security import get_current_user
from app.infrastructure.schemas.user import User


async def get_user_and_tenant(user: User = Depends(get_current_user)):
    return user, str(user.tenant_id)