from sqlalchemy import Column, Integer, String, DateTime, Text

from database.mysql_connection import Base


class EquipamentoMovimentacao(Base):
    """
    Histórico de vínculo entre um colaborador e um ativo (equipamento ou chip).
    O schema original não tinha histórico — id_colaborador ficava direto na
    linha do equipamento/chip, só respondendo "quem tem hoje".

    tipo_ativo: 'equipamento' | 'chip'
    id_ativo:   id do parque_tecnologico OU do chips, conforme tipo_ativo

    Migration necessária:

        CREATE TABLE equipamento_movimentacao (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipo_ativo VARCHAR(20) NOT NULL,
            id_ativo INT NOT NULL,
            id_colaborador INT NOT NULL,
            data_vinculo DATETIME NOT NULL,
            data_devolucao DATETIME NULL,
            observacao TEXT NULL,
            INDEX idx_mov_ativo (tipo_ativo, id_ativo),
            INDEX idx_mov_colaborador (id_colaborador)
        );
    """
    __tablename__ = "equipamento_movimentacao"

    id = Column(Integer, primary_key=True, index=True)
    tipo_ativo = Column(String(20), nullable=False)
    id_ativo = Column(Integer, nullable=False, index=True)
    id_colaborador = Column(Integer, nullable=False, index=True)
    data_vinculo = Column(DateTime, nullable=False)
    data_devolucao = Column(DateTime, nullable=True)
    observacao = Column(Text, nullable=True)
