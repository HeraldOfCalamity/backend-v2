from pydantic import BaseModel, EmailStr


class MailData(BaseModel):
    nombre_especialista: str
    nombre_especialidad: str
    nombre_paciente: str
    fecha: str
    hora: str
    nombre_consultorio: str

class ReceiverData(BaseModel):
    nombre_receptor: str
    email_receptor: EmailStr