CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `vw_bi_pagar` AS
    SELECT 
        `f`.`codigo_raw` AS `codigo`,
        `f`.`id_empresa` AS `id_empresa`,
        `e`.`nome_empresa` AS `nome_empresa`,
        `f`.`id_pessoa` AS `id_pessoa`,
        `p`.`nome` AS `nome_pessoa`,
        `f`.`numero_documento` AS `numero_documento`,
        `f`.`ordem` AS `ordem`,
        `f`.`origem` AS `origem`,
        `f`.`descricao_forma_cobranca` AS `descricao_forma_cobranca`,
        `f`.`valor_total` AS `valor_total`,
        `f`.`data_vencimento` AS `data_vencimento`,
        `f`.`data_baixa` AS `data_baixa`,
        `f`.`dias_atraso` AS `dias_atraso`,
        `f`.`status_financeiro` AS `status_financeiro`,
        `f`.`descricao_situacao` AS `descricao_situacao`,
        `ppo`.`ultima_atualizacao` AS `ultima_atualizacao`
    FROM
        (((`financeiro_bi` `f`
        LEFT JOIN `empresa_bi` `e` ON ((`e`.`codigo_empresa` = `f`.`id_empresa`)))
        LEFT JOIN `pessoa_bi` `p` ON ((`p`.`id_sances` = `f`.`id_pessoa`)))
        LEFT JOIN (SELECT 
            `pipeline_offset`.`tenant_id` AS `tenant_id`,
                MAX(`pipeline_offset`.`ultima_execucao`) AS `ultima_atualizacao`
        FROM
            `pipeline_offset`
        WHERE
            (`pipeline_offset`.`origem` LIKE '%financeiro%')
        GROUP BY `pipeline_offset`.`tenant_id`) `ppo` ON ((`ppo`.`tenant_id` = `f`.`tenant_id`)))
    WHERE
        ((`f`.`tipo_titulo` = 'PAGAR')
            AND (UPPER(`f`.`descricao_situacao`) IN ('EM ABERTO' , 'TRÂNSITO', 'BAIXADO', 'BAIXADO PARCIAL')))