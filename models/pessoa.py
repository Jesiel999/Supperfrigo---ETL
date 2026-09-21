from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

from database.mysql_connection import Base


class PessoaBI(Base):
    __tablename__ = "pessoa_bi"

    id = Column(Integer, primary_key=True, index=True)
    id_sances = Column(Integer)
    id_sults = Column(Integer)
    id_multisys = Column(Integer)
    id_econnect = Column(Integer)
    cpf_cnpj = Column(String(20), unique=True)
    nome = Column(String(255), index=True)
    sexo = Column(String(1))
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    id_nectar = Column(Integer)
    colaborador = Column(Boolean)
