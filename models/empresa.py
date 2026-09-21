from sqlalchemy import Column, Integer, String

from database.mysql_connection import Base


class EmpresaBI(Base):
    __tablename__ = "empresa_bi"

    codigo_empresa = Column(Integer, primary_key=True)
    nome_empresa = Column(String(255), nullable=False)
