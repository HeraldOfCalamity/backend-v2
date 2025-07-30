from beanie import PydanticObjectId
from app.core.exceptions import raise_not_found
from app.domain.entities.officeConfig_entity import OfficeConfigOut, OfficeConfigUpdate
from app.infrastructure.schemas.officeConfig import OfficeConfig


async def get_office_config(tenant_id: str) -> list[OfficeConfig]:
    config = await OfficeConfig.find(OfficeConfig.tenant_id == PydanticObjectId(tenant_id)).to_list()
    return config

async def update_office_config(config_id: str, data: OfficeConfigUpdate, tenant_id: str) -> OfficeConfig:
    config = await OfficeConfig.find_one(OfficeConfig.tenant_id == PydanticObjectId(tenant_id)).find_one(OfficeConfig.id == PydanticObjectId(config_id))
    if not config:
        raise raise_not_found('Configuracion')
    
    config.value = data.value

    await config.save()
    return config
    
def office_config_to_out(office_config: OfficeConfig) -> OfficeConfigOut:
    office_config_dict = office_config.model_dump()
    office_config_dict['id'] = str(office_config.id)
    return OfficeConfigOut(**office_config_dict)
