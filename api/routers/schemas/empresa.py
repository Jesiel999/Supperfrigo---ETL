from pydantic import BaseModel, ConfigDict


class EmpresaBase(BaseModel):
    nome_empresa: str


class EmpresaCreate(EmpresaBase):
    codigo_empresa: int


class EmpresaUpdate(EmpresaBase):
    pass


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    codigo_empresa: int
