from typing import Optional
from pydantic import BaseModel, ConfigDict

class ChipBase(BaseModel):
    id_empresa: int
    id_departamento: Optional[int] = None
    id_colaborador: Optional[int] = None
    numero: Optional[str] = None
    iccid: Optional[str] = None

class ChipCreate(ChipBase):
    pass

class ChipUpdate(ChipBase):
    pass

class ChipOut(ChipBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome_colaborador: Optional[str] = None
    nome_empresa: Optional[str] = None
