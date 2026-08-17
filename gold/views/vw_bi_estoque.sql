CREATE 
    ALGORITHM = UNDEFINED 
    DEFINER = `root`@`localhost` 
    SQL SECURITY DEFINER
VIEW `vw_bi_estoque` AS
    SELECT 
        `emp`.`tenant_id` AS `tenant_id`,
        `emp`.`codigo_empresa` AS `id_empresa`,
        `emp`.`nome_fantasia` AS `empresa_nome`,
        `emp`.`codigo_produto` AS `codigo_produto`,
        `prod`.`produto_descricao` AS `produto_descricao`,
        `prod`.`descricao_categoria` AS `categoria`,
        `prod`.`descricao_grupo` AS `grupo`,
        `emp`.`qtd_estoque` AS `qtd_estoque`,
        (`emp`.`qtd_estoque` * COALESCE(`prc`.`custo_medio`, 0)) AS `valor_estoque_custo`,
        (`emp`.`qtd_estoque` * COALESCE(`prc`.`venda_varejo`, 0)) AS `valor_estoque_venda`,
        (CASE
            WHEN (`emp`.`qtd_estoque` > 0) THEN 1
            ELSE 0
        END) AS `possui_saldo`,
        `ppo`.`ultima_atualizacao` AS `ultima_atualizacao`
    FROM
        (((`estoque_empresa_bi` `emp`
        LEFT JOIN `vw_bi_produto` `prod` ON (((`prod`.`tenant_id` = `emp`.`tenant_id`)
            AND (`prod`.`codigo_produto` = `emp`.`codigo_produto`))))
        LEFT JOIN `estoque_precos_bi` `prc` ON (((`prc`.`tenant_id` = `emp`.`tenant_id`)
            AND (`prc`.`codigo_produto` = `emp`.`codigo_produto`)
            AND (`prc`.`codigo_empresa` = `emp`.`codigo_empresa`)
            AND (`prc`.`data_processamento` = `emp`.`data_processamento`))))
        LEFT JOIN (SELECT 
            `pipeline_offset`.`tenant_id` AS `tenant_id`,
                `pipeline_offset`.`ultima_execucao` AS `ultima_atualizacao`
        FROM
            `pipeline_offset`
        WHERE
            (`pipeline_offset`.`origem` = 'estoque_sances')
        GROUP BY `pipeline_offset`.`tenant_id`) `ppo` ON ((`ppo`.`tenant_id` = `emp`.`tenant_id`)))