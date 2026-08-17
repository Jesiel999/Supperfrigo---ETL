CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `vw_bi_receber` AS
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
        (SELECT 
                MAX(`fb`.`atualizado_em`)
            FROM
                `financeiro_bi` `fb`) AS `ultima_atualizacao`
    FROM
        ((`financeiro_bi` `f`
        LEFT JOIN (SELECT 
            `empresa_bi`.`codigo_empresa` AS `codigo_empresa`,
                MAX(`empresa_bi`.`nome_empresa`) AS `nome_empresa`
        FROM
            `empresa_bi`
        GROUP BY `empresa_bi`.`codigo_empresa`) `e` ON ((`e`.`codigo_empresa` = `f`.`id_empresa`)))
        LEFT JOIN (SELECT 
            `pessoa_bi`.`id_sances` AS `id_sances`,
                MAX(`pessoa_bi`.`nome`) AS `nome`
        FROM
            `pessoa_bi`
        GROUP BY `pessoa_bi`.`id_sances`) `p` ON ((`p`.`id_sances` = `f`.`id_pessoa`)))
    WHERE
        ((`f`.`tipo_titulo` = 'RECEBER')
            AND (UPPER(`f`.`descricao_situacao`) IN ('EM ABERTO' , 'TRÂNSITO', 'BAIXADO', 'BAIXADO PARCIAL')))