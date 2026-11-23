from sqlalchemy import Column, Integer, String

from database.mysql_connection import Base


class EmpresaBI(Base):
    __tablename__ = "slv_empresa"

    codigo_empresa = Column(Integer, primary_key=True)
    nome_empresa = Column(String(255), nullable=False)
