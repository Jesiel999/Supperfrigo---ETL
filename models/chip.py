from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from database.mysql_connection import Base


class Chip(Base):
    __tablename__ = "chips"

    id = Column(Integer, primary_key=True, index=True)
    id_empresa = Column(Integer, ForeignKey("empresa_bi.codigo_empresa"), nullable=False)
    id_departamento = Column(Integer, ForeignKey("dim_departamento.id"), nullable=True)
    id_colaborador = Column(Integer, ForeignKey("pessoa_bi.id"), nullable=True)
    numero = Column(String(50))
    iccid = Column(String(30))

    colaborador = relationship("PessoaBI", foreign_keys=[id_colaborador])
    empresa = relationship("EmpresaBI")
