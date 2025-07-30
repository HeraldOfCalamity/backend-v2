from pydantic import BaseModel, Field


class OfficeConfigUpdate(BaseModel):
    value: str

class OfficeConfigOut(BaseModel):
    id: str
    name: str
    value:str