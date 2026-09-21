from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EquipamentoBase(BaseModel):
    nome: str
    id_empresa: int
    id_tipo: int
    id_departamento: Optional[int] = None
    id_marca: Optional[int] = None
    id_modelo: Optional[int] = None
    id_toner: Optional[int] = None
    id_monitor: Optional[int] = None
    id_colaborador: Optional[int] = None
    senha: Optional[str] = None
    scanner: Optional[bool] = False
    data_fabricacao: Optional[date] = None
    serie: Optional[str] = None
    processador: Optional[str] = None
    memoria_ram: Optional[str] = None
    armazenamento: Optional[str] = None
    tamanho: Optional[str] = None
    so: Optional[str] = None
    ip: Optional[str] = None
    mac: Optional[str] = None
    observacao: Optional[str] = None


class EquipamentoCreate(EquipamentoBase):
    pass


class EquipamentoUpdate(EquipamentoBase):
    pass


class EquipamentoOut(EquipamentoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    nome_empresa: Optional[str] = None
    nome_tipo: Optional[str] = None
    nome_marca: Optional[str] = None
    nome_modelo: Optional[str] = None
    nome_colaborador: Optional[str] = None


class EquipamentoListaOut(BaseModel):
    total: int
    itens: list[EquipamentoOut]


class MovimentacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_colaborador: int
    nome_colaborador: Optional[str] = None
    data_vinculo: datetime
    data_devolucao: Optional[datetime] = None
    observacao: Optional[str] = None


class VincularRequest(BaseModel):
    id_colaborador: int
    observacao: Optional[str] = None


class DevolverRequest(BaseModel):
    observacao: Optional[str] = None


class ResumoEquipamentos(BaseModel):
    total: int
    ativos: int
    inativos: int
    sem_colaborador: int
    por_tipo: dict[str, int]
    por_empresa: dict[str, int]
