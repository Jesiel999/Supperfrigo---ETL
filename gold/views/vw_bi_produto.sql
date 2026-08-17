CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `vw_bi_produto` AS
    SELECT 
        `p`.`tenant_id` AS `tenant_id`,
        `p`.`codigo_produto` AS `codigo_produto`,
        `p`.`descricao` AS `produto_descricao`,
        `p`.`referencia` AS `referencia`,
        `p`.`referencia_fabrica` AS `referencia_fabrica`,
        `p`.`sigla_unidade_medida` AS `sigla_unidade_medida`,
        `p`.`descricao_unidade_medida` AS `descricao_unidade_medida`,
        `p`.`codigo_categoria` AS `codigo_categoria`,
        `p`.`descricao_categoria` AS `descricao_categoria`,
        `p`.`descricao_grupo` AS `descricao_grupo`,
        `p`.`descricao_subgrupo` AS `descricao_subgrupo`,
        `p`.`codigo_ean` AS `codigo_ean`,
        `p`.`codigo_barras` AS `codigo_barras`,
        `p`.`ativo` AS `ativo`,
        `p`.`data_processamento` AS `data_processamento`
    FROM
        (`estoque_produto_bi` `p`
        JOIN (SELECT 
            `estoque_produto_bi`.`tenant_id` AS `tenant_id`,
                `estoque_produto_bi`.`codigo_produto` AS `codigo_produto`,
                `estoque_produto_bi`.`data_processamento` AS `max_dt`
        FROM
            `estoque_produto_bi`
        GROUP BY `estoque_produto_bi`.`tenant_id` , `estoque_produto_bi`.`codigo_produto`) `ult` ON (((`ult`.`tenant_id` = `p`.`tenant_id`)
            AND (`ult`.`codigo_produto` = `p`.`codigo_produto`)
            AND (`ult`.`max_dt` = `p`.`data_processamento`))))