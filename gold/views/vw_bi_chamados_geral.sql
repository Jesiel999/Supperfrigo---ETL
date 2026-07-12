-- ============================================================
-- vw_chamados_dashboard
-- View de leitura para o Dashboard de Chamados.
-- Junta chamados_geral_gold (que já traz os campos calculados:
-- tempo_resolucao, sla_horas, sla_cumprido, horas_atrasado,
-- tipo_solicitacao) com dim_departamento para trazer o nome
-- legível do departamento.
--
-- OBS: os códigos do CASE de `situacao` são um exemplo — ajuste
-- para os valores reais usados na sua base (1=Aberto, 2=Em
-- andamento, 3=Resolvido, 4=Concluído, 5=Cancelado).
--
-- TODO (ajustar para as tabelas reais do seu banco):
-- 1) `dim_pessoa` — não veio no schema enviado. É necessária para
--    resolver nome_solicitante / nome_responsavel a partir de
--    solicitante_id / responsavel_id. Se não existir, crie uma
--    dimensão de pessoas ou troque o join pela tabela certa.
-- 2) `unidade_id` só existe em chamados_bi (chamados_geral_gold
--    não tem essa coluna). Se "unidade" e "empresa" forem o mesmo
--    conceito com nomes diferentes por sistema, pode remover o
--    join de unidade e usar directly empresa_id/nome_departamento.
--    Se forem conceitos distintos, ajuste o join de dim_unidade.
-- ============================================================

CREATE OR REPLACE VIEW vw_chamados_dashboard AS
SELECT
    c.id,
    c.codigo,
    c.titulo,
    c.tipo,
    c.situacao,
    CASE c.situacao
        WHEN 1 THEN 'ABERTO'
        WHEN 2 THEN 'EM_ANDAMENTO'
        WHEN 3 THEN 'RESOLVIDO'
        WHEN 4 THEN 'CONCLUIDO'
        WHEN 5 THEN 'CANCELADO'
        ELSE 'DESCONHECIDO'
    END                                 AS situacao_desc,

    c.solicitante_id,
    ps.nome                             AS nome_solicitante,   -- TODO: ajustar dim_pessoa

    c.responsavel_id,
    pr.nome                             AS nome_responsavel,   -- TODO: ajustar dim_pessoa

    c.empresa_id,

    cb.unidade_id,                                             -- TODO: confirmar origem
    u.nome                              AS nome_unidade,       -- TODO: ajustar dim_unidade

    c.departamento_id,
    d.nome                              AS nome_departamento,
    c.departamento_envio_id,

    c.assunto_id,

    c.data_aberto,
    c.data_resolvido,
    c.data_concluido,
    c.data_resolver_planejado,
    c.data_resolver_estipulado,

    c.data_primeira_interacao,
    c.data_ultima_alteracao,

    c.avaliacao_nota,
    c.avaliacao_observacao,

    c.quantidade_interacao_publico,
    c.quantidade_interacao_interno,

    -- Campos já calculados na gold
    c.tempo_primeira_resposta,          -- minutos
    c.tempo_resolucao,                  -- minutos
    c.sla_horas,
    c.sla_cumprido,
    c.horas_atrasado,
    c.horas_resolver,
    c.tipo_solicitacao

FROM chamados_geral_gold c
LEFT JOIN dim_departamento d
       ON d.departamento_id = c.departamento_id
      AND d.empresa_id      = c.empresa_id

-- TODO: criar/ajustar dim_pessoa (id, nome) — usada para solicitante e responsável
LEFT JOIN dim_pessoa ps
       ON ps.id = c.solicitante_id
LEFT JOIN dim_pessoa pr
       ON pr.id = c.responsavel_id

-- TODO: unidade_id vem de chamados_bi (não existe em chamados_geral_gold);
-- ajuste a chave de join conforme a relação real entre as duas tabelas
LEFT JOIN chamados_bi cb
       ON cb.codigo_raw = c.codigo
LEFT JOIN dim_unidade u
       ON u.id = cb.unidade_id;


-- ============================================================
-- (Opcional) view de etiquetas por chamado, caso o front precise
-- filtrar/mostrar etiquetas na tabela.
-- ============================================================
CREATE OR REPLACE VIEW vw_chamados_etiquetas AS
SELECT
    ce.empresa_id,
    ce.chamado_codigo,
    et.etiqueta_id,
    et.nome AS etiqueta_nome,
    et.cor  AS etiqueta_cor
FROM chamados_etiqueta_bi ce
JOIN dim_etiqueta et
  ON et.etiqueta_id = ce.etiqueta_id;