from pydantic import BaseModel, ConfigDict


class DropdownItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class NomeSimplesPayload(BaseModel):
    """Payload de criação/edição para cadastros no formato (id, nome):
    Marca, Modelo, Toner, Departamento."""
    nome: str
