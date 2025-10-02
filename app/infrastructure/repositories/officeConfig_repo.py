from zoneinfo import ZoneInfo
from beanie import PydanticObjectId
from beanie.operators import And
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

async def get_office_config_by_name(name: str, tenant_id: str) -> OfficeConfig:
    return await OfficeConfig.find_one(And(
        OfficeConfig.tenant_id == PydanticObjectId(tenant_id),
        OfficeConfig.name == name
    ))

def office_config_to_out(office_config: OfficeConfig) -> OfficeConfigOut:
    office_config_dict = office_config.model_dump()
    office_config_dict['id'] = str(office_config.id)
    return OfficeConfigOut(**office_config_dict)

async def is_auto_cancel_enabled(tenant_id: str, default: bool = False) -> bool:
    oc = await get_office_config_by_name('auto_cancelacion_habilitada', tenant_id)
    if not oc or oc.value not in ('0', '1'):
        return default
    
    return oc.value == '1'

async def get_office_timezone(tenant_id: str, default_tz: str = 'America/La_Paz') -> ZoneInfo:
    oc = await get_office_config_by_name('office_timezone', tenant_id)
    tzname = oc.value if oc and oc.value else default_tz
    return ZoneInfo(tzname)