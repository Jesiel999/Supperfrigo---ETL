from sqlalchemy import (
    Column, Integer, String, Boolean, Date, Text, ForeignKey
)
from sqlalchemy.orm import relationship

from database.mysql_connection import Base


class TipoEquipamento(Base):
    __tablename__ = "tipo_equipamento"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)


class Marca(Base):
    __tablename__ = "marca"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)


class Modelo(Base):
    __tablename__ = "modelo"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)


class Toner(Base):
    __tablename__ = "toner"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)


class ParqueTecnologico(Base):
    """
    Tabela única para notebook/desktop, impressora, monitor, celular etc.
    Campos técnicos (processador, memoria_ram, so, mac...) foram tornados
    opcionais para servir também a equipamentos que não são computadores.

    ATENÇÃO: `mac` e `serie` eram NOT NULL no schema original. Se ainda
    estiverem NOT NULL no banco, rode a migration abaixo antes de usar
    este endpoint com impressoras/celulares:

        ALTER TABLE parque_tecnologico MODIFY mac VARCHAR(17) NULL;
        ALTER TABLE parque_tecnologico MODIFY serie VARCHAR(255) NULL;
        ALTER TABLE parque_tecnologico ADD COLUMN ativo BOOLEAN NOT NULL DEFAULT TRUE;
    """
    __tablename__ = "parque_tecnologico"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    id_colaborador = Column(Integer, ForeignKey("pessoa_bi.id"), nullable=True)
    senha = Column(String(255))
    id_empresa = Column(Integer, ForeignKey("empresa_bi.codigo_empresa"), nullable=False)
    id_departamento = Column(Integer, ForeignKey("dim_departamento.id"), nullable=True)
    id_tipo = Column(Integer, ForeignKey("tipo_equipamento.id"), nullable=False)
    id_monitor = Column(Integer, ForeignKey("parque_tecnologico.id"), nullable=True)
    id_marca = Column(Integer, ForeignKey("marca.id"), nullable=True)
    id_modelo = Column(Integer, ForeignKey("modelo.id"), nullable=True)
    id_toner = Column(Integer, ForeignKey("toner.id"), nullable=True)
    scanner = Column(Boolean, default=False)
    data_fabricacao = Column(Date, nullable=True)
    serie = Column(String(255), nullable=True)
    processador = Column(String(255), nullable=True)
    memoria_ram = Column(String(100), nullable=True)
    armazenamento = Column(String(100), nullable=True)
    tamanho = Column(String(100), nullable=True)
    so = Column(String(100), nullable=True)
    ip = Column(String(45), nullable=True)
    mac = Column(String(17), nullable=True)
    observacao = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)

    tipo = relationship("TipoEquipamento")
    marca_rel = relationship("Marca")
    modelo_rel = relationship("Modelo")
    toner_rel = relationship("Toner")
    colaborador = relationship("PessoaBI", foreign_keys=[id_colaborador])
    empresa = relationship("EmpresaBI")
