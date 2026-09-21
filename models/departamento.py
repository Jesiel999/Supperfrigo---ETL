from sqlalchemy import Column, Integer, String

from database.mysql_connection import Base


class DimDepartamento(Base):
    """
    Essa tabela é referenciada nos Refs do seu DBML (dim_departamento)
    mas não estava definida. Ajuste os campos conforme o real schema
    já existente no banco, se ele já existir.
    """
    __tablename__ = "dim_departamento"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
