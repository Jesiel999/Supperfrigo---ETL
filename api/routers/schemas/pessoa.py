from typing import Optional
from pydantic import BaseModel, ConfigDict

class PessoaBase(BaseModel):
    nome: str
    cpf_cnpj: Optional[str] = None
    sexo: Optional[str] = None
    colaborador: bool = True

class PessoaCreate(PessoaBase):
    pass

class PessoaUpdate(PessoaBase):
    pass

class PessoaOut(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: int

class PessoaListaOut(BaseModel):
    total: int
    itens: list[PessoaOut]
