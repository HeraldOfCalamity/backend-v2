from app.infrastructure.schemas.office import Office


async def get_benedetta_office():
    return await Office.find_one(Office.name == 'Benedetta Bellezza');