CREATE OR REPLACE VIEW vw_bi_chamados AS
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
    ps.nome                             AS nome_solicitante,  
    c.responsavel_id,
    pr.nome                             AS nome_responsavel,   
       
    c.empresa_id,

    cb.unidade_id,                                            
    u.nome                              AS nome_unidade,       

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

    c.tempo_primeira_resposta,         
    c.tempo_resolucao,                  
    c.sla_horas,
    c.sla_cumprido,
    c.horas_atrasado,
    c.horas_resolver,
    c.tipo_solicitacao

FROM chamados_geral_gold c
LEFT JOIN dim_departamento d
       ON d.departamento_id = c.departamento_id
      AND d.empresa_id      = c.empresa_id

LEFT JOIN pessoa_bi ps
       ON ps.id_sults = c.solicitante_id
LEFT JOIN pessoa_bi pr
       ON pr.id_sults = c.responsavel_id

LEFT JOIN chamados_bi cb
       ON cb.codigo_raw = c.codigo
LEFT JOIN pessoa_bi u
       ON u.id_sults = cb.unidade_id;

CREATE OR REPLACE VIEW vw_bi_etiquetas AS
SELECT
    ce.empresa_id,
    ce.chamado_codigo,
    et.etiqueta_id,
    et.nome AS etiqueta_nome,
    et.cor  AS etiqueta_cor
FROM chamados_etiqueta_bi ce
JOIN dim_etiqueta et
  ON et.etiqueta_id = ce.etiqueta_id;