from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ItemEquipamento(BaseModel):
    id: int
    # Campos que não existem em parque_tecnologico mas aparecem no termo impresso
    cor: Optional[str] = None
    condicao: Optional[str] = None          # Novo, Seminovo, Usado...


class GerarTermoRequest(BaseModel):
    id_modelo: int
    id_empresa: int
    id_colaborador: int
    equipamentos: list[ItemEquipamento] = Field(default_factory=list)
    ids_chips: list[int] = Field(default_factory=list)
    # ex.: {"carregador": true, "mouse": true, "monitor": false}
    acessorios: dict[str, bool] = Field(default_factory=dict)
    data_emissao: Optional[date] = None
    formato: Literal["pdf", "docx"] = "pdf"

    @model_validator(mode="after")
    def _ao_menos_um_item(self):
        if not self.equipamentos and not self.ids_chips:
            raise ValueError("Selecione ao menos um equipamento ou chip")
        return self


class ModeloOut(BaseModel):
    id: int
    slug: str
    nome: str
    descricao: Optional[str] = None
    versao: int
    ativo: bool
    atualizado_em: Optional[datetime] = None


class EmpresaTermoDados(BaseModel):
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None
    cnpj: Optional[str] = None
    ie: Optional[str] = None
    endereco: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(default=None, max_length=2)
    cep: Optional[str] = None
    telefone: Optional[str] = None


class EmpresaTermoOut(EmpresaTermoDados):
    codigo_empresa: int
    nome_empresa: str


class TermoEmitidoOut(BaseModel):
    id: int
    id_modelo: int
    nome_modelo: Optional[str] = None
    versao_modelo: int
    id_empresa: int
    id_colaborador: int
    nome_colaborador: Optional[str] = None
    ids_equipamentos: list[int]
    ids_chips: list[int]
    gerado_por: Optional[str] = None
    gerado_em: datetime
    tem_assinado: bool
