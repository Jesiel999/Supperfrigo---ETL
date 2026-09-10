CREATE TABLE IF NOT EXISTS `chamados_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` int NOT NULL,
  `titulo` text,
  `solicitante_id` int,
  `solicitante_nome` varchar(255),
  `responsavel_id` int,
  `responsavel_nome` varchar(255),
  `unidade_id` int,
  `unidade_nome` varchar(255),
  `departamento_id` int,
  `departamento_nome` varchar(100),
  `departamento_envio_id` int,
  `departamento_envio_nome` varchar(100),
  `assunto_id` int,
  `assunto_nome` varchar(255),
  `tipo` int,
  `data_aberto` varchar(20),
  `data_resolvido` varchar(20),
  `data_concluido` varchar(20),
  `data_resolver_planejado` varchar(20),
  `data_resolver_estipulado` varchar(20),
  `avaliacao_nota` int,
  `avaliacao_observacao` text,
  `situacao` int,
  `data_primeira_interacao` varchar(20),
  `data_ultima_alteracao` varchar(20),
  `quantidade_interacao_publico` int,
  `quantidade_interacao_interno` int,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP),
  `atualizado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `chamados_apoio_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `chamado_codigo` int NOT NULL,
  `pessoa_id` int,
  `pessoa_nome` varchar(255),
  `departamento_id` int,
  `departamento_nome` varchar(100),
  `pessoa_unidade` boolean,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `chamados_etiqueta_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `chamado_codigo` int NOT NULL,
  `etiqueta_id` int,
  `etiqueta_nome` varchar(255),
  `etiqueta_cor` varchar(20),
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `pos_venda_raw` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codigo_origem` bigint UNIQUE NOT NULL,
  `tipo` int NOT NULL,
  `descricao_tipo` varchar(100),
  `orcamento_os` boolean NOT NULL DEFAULT false,
  `numero` bigint,
  `codigo_situacao` varchar(10),
  `situacao` varchar(100),
  `aguardando_liberacao` boolean NOT NULL DEFAULT false,
  `codigo_empresa` bigint,
  `nome_empresa` varchar(255),
  `codigo_cliente` bigint,
  `nome_cliente` varchar(255),
  `codigo_tipo_preco` bigint,
  `descricao_tipo_preco` varchar(255),
  `codigo_veiculo` bigint,
  `placa_veiculo` varchar(20),
  `codigo_modelo_veiculo` bigint,
  `descricao_modelo_veiculo` varchar(255),
  `codigo_cor_veiculo` bigint,
  `descricao_cor_veiculo` varchar(255),
  `ano_fabricacao_veiculo` smallint,
  `ano_modelo_veiculo` smallint,
  `codigo_tipo_os` bigint,
  `descricao_tipo_os` varchar(255),
  `km_entrada` decimal(15,2),
  `km_saida` decimal(15,2),
  `data_entrada` datetime,
  `data_saida` datetime,
  `solicitacao_cliente` text,
  `avaria` text,
  `defeito_averiguado` text,
  `codigo_proprietario` bigint,
  `nome_proprietario` varchar(255),
  `codigo_tipo_midia` bigint,
  `descricao_tipo_midia` varchar(255),
  `codigo_modalidade_venda` bigint,
  `descricao_modalidade_venda` varchar(255),
  `codigo_conveniado` bigint,
  `nome_conveniado` varchar(255),
  `codigo_consultor` bigint,
  `nome_consultor` varchar(255),
  `percentual_comissao_peca` decimal(10,4),
  `valor_comissao_peca_consultor` decimal(15,2),
  `percentual_comissao_servico` decimal(10,4),
  `valor_comissao_servico_consultor` decimal(15,2),
  `total_comissao_consultor` decimal(15,2),
  `observacao` text,
  `observacao_nota` text,
  `codigo_usuario_insercao` bigint,
  `nome_usuario_insercao` varchar(255),
  `data_insercao` datetime,
  `codigo_usuario_alteracao` bigint,
  `nome_usuario_alteracao` varchar(255),
  `data_alteracao` datetime,
  `codigo_usuario_cancelamento` bigint,
  `nome_usuario_cancelamento` varchar(255),
  `data_cancelamento` datetime,
  `codigo_usuario_fechamento` bigint,
  `nome_usuario_fechamento` varchar(255),
  `data_fechamento` datetime,
  `valor_seguro` decimal(15,2),
  `valor_frete` decimal(15,2),
  `valor_despesas` decimal(15,2),
  `valor_acrescimo_financeiro` decimal(15,2),
  `total_pecas_bruto` decimal(15,2),
  `total_desconto_pecas` decimal(15,2),
  `total_pecas_liquido` decimal(15,2),
  `total_pecas_custo` decimal(15,2),
  `total_pecas_lucro` decimal(15,2),
  `total_servicos_bruto` decimal(15,2),
  `total_desconto_servicos` decimal(15,2),
  `total_servicos_liquido` decimal(15,2),
  `total_servicos_custo` decimal(15,2),
  `total_servicos_lucro` decimal(15,2),
  `total_geral` decimal(15,2),
  `codigo_condicao_pagamento` bigint,
  `descricao_condicao_pagamento` varchar(255),
  `created_at` datetime,
  `updated_at` datetime,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `pos_venda_peca_raw` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codposv` bigint NOT NULL,
  `codigo_peca` bigint,
  `referencia_peca` varchar(100),
  `descricao_peca` varchar(255),
  `unidade_peca` varchar(30),
  `qtd_peca` decimal(15,4),
  `valor_unitario` decimal(15,4),
  `custo_unitario` decimal(15,4),
  `custo_total` decimal(15,2),
  `total_bruto` decimal(15,2),
  `valor_desconto` decimal(15,2),
  `total_liquido` decimal(15,2),
  `codigo_mecanico` bigint,
  `nome_mecanico` varchar(255),
  `percentual_comissao_mecanico` decimal(10,4),
  `valor_comissao_mecanico` decimal(15,2),
  `peca_cancelada` boolean NOT NULL DEFAULT false,
  `codigo_motivo_cancelamento` bigint,
  `descricao_motivo_cancelamento` varchar(255),
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `pos_venda_servico_raw` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codposv` bigint NOT NULL,
  `codigo_servico` bigint,
  `referencia_servico` varchar(100),
  `descricao_servico` varchar(255),
  `unidade_servico` varchar(30),
  `qtd_servico` decimal(15,4),
  `valor_unitario` decimal(15,4),
  `custo_unitario` decimal(15,4),
  `custo_total` decimal(15,2),
  `total_bruto` decimal(15,2),
  `valor_desconto` decimal(15,2),
  `total_liquido` decimal(15,2),
  `codigo_mecanico` bigint,
  `nome_mecanico` varchar(255),
  `percentual_comissao_mecanico` decimal(10,4),
  `valor_comissao_mecanico` decimal(15,2),
  `servico_cancelado` boolean NOT NULL DEFAULT false,
  `codigo_motivo_cancelamento` bigint,
  `descricao_motivo_cancelamento` varchar(255),
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `pos_venda_nota_raw` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codposv` bigint NOT NULL,
  `tipo` varchar(20),
  `descricao` varchar(255),
  `codigo_nota` bigint,
  `numero_nota` bigint,
  `chave_nota` varchar(100),
  `data_faturamento` datetime,
  `operacao` varchar(255),
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `pos_venda_parcela_raw` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codposv` bigint NOT NULL,
  `tipo_parcela` enum(PECA,SERVICO,FRANQUIA),
  `ordem_parcela` varchar(20),
  `vencimento_parcela` date,
  `forma_cobranca_parcela` varchar(255),
  `valor_parcela` decimal(15,2),
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `telemetria_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` bigint NOT NULL,
  `dispositivo_id` varchar(100),
  `veiculo_id` bigint NOT NULL,
  `data_evento` datetime(3),
  `gsm_signal` int,
  `data_mode` int,
  `speed` int,
  `external_voltage` int,
  `battery_voltage` int,
  `battery_current` int,
  `gnss_status` boolean,
  `brake_switch` boolean,
  `wheel_based_speed` decimal(10,3),
  `cruise_control_active` boolean,
  `clutch_switch` boolean,
  `pto_state` int,
  `acceleration_pedal_position` decimal(10,3),
  `engine_current_load` decimal(10,3),
  `engine_total_fuel_used` decimal(16,3),
  `fuel_level` decimal(10,3),
  `engine_speed` decimal(10,3),
  `diagnostics_supported` boolean,
  `requests_supported` boolean,
  `direction_indication` int,
  `tachograph_performance` int,
  `handling_info` int,
  `system_event` int,
  `engine_coolant_temperature` decimal(10,3),
  `fuel_rate` decimal(10,3),
  `instantaneous_fuel_economy` decimal(10,3),
  `high_resolution_engine_total_fuel_used` decimal(16,3),
  `gnss_pdop` decimal(10,3),
  `gnss_hdop` decimal(10,3),
  `sleep_mode` boolean,
  `data_ingestao` datetime(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3)),
  `processado` boolean NOT NULL DEFAULT false,
  `data_processamento` datetime(3),
  `criado_em` datetime(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3)),
  `atualizado_em` datetime(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3))
);

CREATE TABLE IF NOT EXISTS `pessoa_sances_raw` (
  `codigo_cliente` int PRIMARY KEY,
  `tipo` varchar(10),
  `cpf_cnpj` varchar(255),
  `nome_cliente` varchar(255),
  `sexo` varchar(30)
);

CREATE TABLE IF NOT EXISTS `email_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `tipo` varchar(20),
  `email` varchar(500)
);

CREATE TABLE IF NOT EXISTS `endereco_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `rua` varchar(255),
  `numero` varchar(50),
  `complemento` varchar(255),
  `bairro` varchar(255),
  `cidade` varchar(100),
  `uf` varchar(10),
  `cep` varchar(10)
);

CREATE TABLE IF NOT EXISTS `telefone_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `celular` varchar(20),
  `comercial` varchar(20),
  `residencial` varchar(20)
);

CREATE TABLE IF NOT EXISTS `financeiro_raw` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint UNIQUE NOT NULL,
  `tipo_titulo` varchar(20),
  `codigo_empresa` varchar(50),
  `nome_empresa` varchar(255),
  `codigo_situacao` varchar(50),
  `descricao_situacao` varchar(255),
  `codigo_pessoa` varchar(50),
  `nome_pessoa` varchar(255),
  `codigo_cliente_fornecedor` varchar(50),
  `nome_cliente_fornecedor` varchar(255),
  `titulo_previsao` varchar(10),
  `criado_manualmente` varchar(10),
  `origem` varchar(100),
  `codigo_origem` varchar(50),
  `numero_documento` varchar(100),
  `ordem` varchar(50),
  `codigo_forma_cobranca` varchar(50),
  `descricao_forma_cobranca` varchar(255),
  `codigo_vendedor` varchar(50),
  `descricao_vendedor` varchar(255),
  `historico` text,
  `codigo_grupo` varchar(50),
  `descricao_grupo` varchar(255),
  `codigo_departamento` varchar(50),
  `descricao_departamento` varchar(255),
  `observacao` text,
  `observacoes_boleto` text,
  `codigo_barras` varchar(100),
  `codigo_forma_pagamento` varchar(50),
  `descricao_forma_pagamento` varchar(255),
  `codigo_categoria_financeira` varchar(50),
  `descricao_categoria_financeira` varchar(255),
  `codigo_convenio` varchar(50),
  `descricao_convenio` varchar(255),
  `codigo_conveniado` varchar(50),
  `descricao_conveniado` varchar(255),
  `codigo_aprovador` varchar(50),
  `nome_aprovador` varchar(255),
  `nosso_numero` varchar(100),
  `numero_remessa` varchar(100),
  `titulo_origem` varchar(100),
  `titulo_gerado` varchar(100),
  `codigo_conta_patrimonial` varchar(50),
  `numero_conta_patrimonial` varchar(100),
  `descricao_conta_patrimonial` varchar(255),
  `codigo_conta_resultado` varchar(50),
  `numero_conta_resultado` varchar(100),
  `descricao_conta_resultado` varchar(255),
  `codigo_centro_custo` varchar(50),
  `descricao_centro_custo` varchar(255),
  `data_emissao` datetime,
  `data_competencia` datetime,
  `data_vencimento` datetime,
  `codigo_usuario_insercao` varchar(50),
  `nome_usuario_insercao` varchar(255),
  `data_insercao` datetime,
  `codigo_usuario_alteracao` varchar(50),
  `nome_usuario_alteracao` varchar(255),
  `data_alteracao` datetime,
  `codigo_usuario_cancelamento` varchar(50),
  `nome_usuario_cancelamento` varchar(255),
  `data_cancelamento` datetime,
  `motivo_cancelamento` text,
  `codigo_usuario_baixa` varchar(50),
  `nome_usuario_baixa` varchar(255),
  `data_baixa` datetime,
  `codigo_usuario_aprovacao` varchar(50),
  `nome_usuario_aprovacao` varchar(255),
  `data_aprovacao` datetime,
  `valor_nominal` decimal(15,2),
  `valor_multa` decimal(15,2),
  `percentual_multa` decimal(10,4),
  `percentual_juros` decimal(10,4),
  `taxa_boleto` decimal(15,2),
  `juros_crediario_proprio` decimal(15,2),
  `acrescimo` decimal(15,2),
  `valor_total` decimal(15,2),
  `valor_baixado` decimal(15,2),
  `valor_nominal_baixado` decimal(15,2),
  `desconto_baixa` decimal(15,2),
  `acrescimo_baixa` decimal(15,2),
  `juros_baixa` decimal(15,2),
  `multa_baixa` decimal(15,2),
  `iof_baixa` decimal(15,2),
  `retencao_total` decimal(15,2)
);

CREATE TABLE IF NOT EXISTS `recebimentos_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `codigo_titulo` bigint,
  `codigo_tipo_movimentacao` int,
  `descricao_tipo_movimentacao` varchar(30),
  `valor_pago` decimal(15,2),
  `valor_nominal` decimal(15,2),
  `data_movimentacao` date,
  `codigo_conta` int,
  `descricao_conta` varchar(50),
  `historico` TEXT,
  `data_conciliacao` datetime,
  `codigo_caixa` int,
  `codigo_cheque_terceiro` int,
  `codigo_pagamento_cartao` int,
  `desconto` decimal(15,2),
  `acrescimo` decimal(15,2),
  `juros` decimal(15,2),
  `multa` decimal(15,2)
);

CREATE TABLE IF NOT EXISTS `modelo_veiculo_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `offset_pagina` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_modelo` int,
  `descricao_modelo` varchar(255),
  `data_extracao` datetime NOT NULL,
  `processado_em` datetime,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `preco_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `offset_pagina` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_empresa` int NOT NULL,
  `cnpj` varchar(20),
  `nome_razao` varchar(255),
  `nome_fantasia` varchar(255),
  `apelido` varchar(100),
  `custo_medio` decimal(14,4),
  `venda_varejo` decimal(14,4),
  `venda_atacado` decimal(14,4),
  `venda_ecommerce` decimal(14,4),
  `garantia` decimal(14,4),
  `sugerido` decimal(14,4),
  `reposicao` decimal(14,4),
  `promocao` decimal(14,4),
  `personalizado1` decimal(14,4),
  `personalizado3` decimal(14,4),
  `data_extracao` datetime NOT NULL,
  `processado_em` datetime,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `produto_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `offset_pagina` int NOT NULL,
  `codigo` int NOT NULL,
  `descricao` varchar(255),
  `referencia` varchar(100),
  `referencia_fabrica` text,
  `endereco_setor` varchar(50),
  `endereco_rua` varchar(50),
  `endereco_andar` varchar(50),
  `sigla_unidade_medida` varchar(10),
  `descricao_unidade_medida` varchar(50),
  `codigo_categoria` int,
  `descricao_categoria` varchar(100),
  `descricao_grupo` varchar(100),
  `descricao_subgrupo` varchar(100),
  `codigo_ean` varchar(50),
  `codigo_barras` varchar(50),
  `ativo` tinyint,
  `data_extracao` datetime NOT NULL,
  `processado_em` datetime,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `quantidade_sances_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `offset_pagina` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_empresa` int NOT NULL,
  `cnpj` varchar(20),
  `nome_razao` varchar(255),
  `nome_fantasia` varchar(255),
  `apelido` varchar(100),
  `qtd_estoque` decimal(14,4),
  `qtd_aplicadas` decimal(14,4),
  `qtd_reservada` decimal(14,4),
  `qtd_transito` decimal(14,4),
  `qtd_pedido` decimal(14,4),
  `qtd_bo` decimal(14,4),
  `data_extracao` datetime NOT NULL,
  `processado_em` datetime,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `tenant` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `nome` varchar(120) NOT NULL,
  `slug` varchar(60) NOT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT '1'
);

CREATE TABLE IF NOT EXISTS `pessoa_sults_raw` (
  `id` int PRIMARY KEY,
  `nome` varchar(255),
  `ativo` boolean,
  `sexo` varchar(1),
  `cpf` varchar(255),
  `celular` varchar(100),
  `telefone` varchar(100),
  `email` varchar(100),
  `dtCadastro` varchar(30),
  `dtUltimaAlteracao` varchar(30),
  `dtInativacao` varchar(30)
);

CREATE TABLE IF NOT EXISTS `endereco_sults_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `uf` varchar(10),
  `cidade` varchar(100),
  `complemento` varchar(255),
  `numero` varchar(50),
  `bairro` varchar(255),
  `cep` varchar(10),
  `rua` varchar(255)
);

CREATE TABLE IF NOT EXISTS `empresa_sults_raw` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `qualificacao_nome` varchar(100),
  `qualificacao_id` int,
  `nomeFantasia_id` int,
  `nomeFantasia_cargo_nome` varchar(100),
  `nomeFantasia_cargo_id` int
);

CREATE UNIQUE INDEX `uk_chamado` ON `chamados_raw` (`tenant_id`, `codigo`);

CREATE INDEX `idx_chamado` ON `chamados_apoio_raw` (`tenant_id`, `chamado_codigo`);

CREATE INDEX `idx_chamado` ON `chamados_etiqueta_raw` (`tenant_id`, `chamado_codigo`);

CREATE UNIQUE INDEX `pos_venda_raw_index_3` ON `pos_venda_raw` (`codigo_origem`);

CREATE INDEX `pos_venda_raw_index_4` ON `pos_venda_raw` (`data_insercao`);

CREATE INDEX `pos_venda_raw_index_5` ON `pos_venda_raw` (`data_alteracao`);

CREATE INDEX `pos_venda_raw_index_6` ON `pos_venda_raw` (`codigo_empresa`);

CREATE INDEX `pos_venda_raw_index_7` ON `pos_venda_raw` (`codigo_cliente`);

CREATE INDEX `pos_venda_raw_index_8` ON `pos_venda_raw` (`codigo_consultor`);

CREATE INDEX `pos_venda_raw_index_9` ON `pos_venda_raw` (`codigo_situacao`);

CREATE INDEX `pos_venda_raw_index_10` ON `pos_venda_raw` (`numero`);

CREATE INDEX `pos_venda_peca_raw_index_11` ON `pos_venda_peca_raw` (`codposv`);

CREATE INDEX `pos_venda_peca_raw_index_12` ON `pos_venda_peca_raw` (`codigo_peca`);

CREATE INDEX `pos_venda_servico_raw_index_13` ON `pos_venda_servico_raw` (`codposv`);

CREATE INDEX `pos_venda_servico_raw_index_14` ON `pos_venda_servico_raw` (`codigo_servico`);

CREATE INDEX `pos_venda_nota_raw_index_15` ON `pos_venda_nota_raw` (`codposv`);

CREATE INDEX `pos_venda_nota_raw_index_16` ON `pos_venda_nota_raw` (`codigo_nota`);

CREATE INDEX `pos_venda_nota_raw_index_17` ON `pos_venda_nota_raw` (`numero_nota`);

CREATE INDEX `pos_venda_parcela_raw_index_18` ON `pos_venda_parcela_raw` (`codposv`);

CREATE INDEX `pos_venda_parcela_raw_index_19` ON `pos_venda_parcela_raw` (`tipo_parcela`);

CREATE INDEX `pos_venda_parcela_raw_index_20` ON `pos_venda_parcela_raw` (`vencimento_parcela`);

CREATE INDEX `idx_telemetria_raw_tenant_data` ON `telemetria_raw` (`tenant_id`, `data_evento`);

CREATE INDEX `idx_telemetria_raw_veiculo_data` ON `telemetria_raw` (`veiculo_id`, `data_evento`);

CREATE INDEX `idx_telemetria_raw_processado` ON `telemetria_raw` (`processado`);

CREATE INDEX `idx_email_sances_pessoa` ON `email_sances_raw` (`pessoa_id`);

CREATE INDEX `idx_endereco_sances_pessoa` ON `endereco_sances_raw` (`pessoa_id`);

CREATE INDEX `idx_telefone_sances_pessoa` ON `telefone_sances_raw` (`pessoa_id`);

CREATE INDEX `idx_codigo_empresa` ON `financeiro_raw` (`codigo_empresa`);

CREATE INDEX `idx_codigo_pessoa` ON `financeiro_raw` (`codigo_pessoa`);

CREATE INDEX `idx_tipo_titulo` ON `financeiro_raw` (`tipo_titulo`);

CREATE INDEX `idx_codigo_situacao` ON `financeiro_raw` (`codigo_situacao`);

CREATE INDEX `idx_data_vencimento` ON `financeiro_raw` (`data_vencimento`);

CREATE INDEX `idx_data_baixa` ON `financeiro_raw` (`data_baixa`);

CREATE INDEX `idx_data_alteracao` ON `financeiro_raw` (`data_alteracao`);

CREATE INDEX `idx_modelo_veiculo_sances_raw_pendente` ON `modelo_veiculo_sances_raw` (`tenant_id`, `processado_em`);

CREATE INDEX `idx_modelo_veiculo_sances_raw_produto` ON `modelo_veiculo_sances_raw` (`tenant_id`, `codigo_produto`);

CREATE INDEX `idx_preco_sances_raw_pendente` ON `preco_sances_raw` (`tenant_id`, `processado_em`);

CREATE INDEX `idx_preco_sances_raw_produto` ON `preco_sances_raw` (`tenant_id`, `codigo_produto`);

CREATE INDEX `idx_produto_sances_raw_pendente` ON `produto_sances_raw` (`tenant_id`, `processado_em`);

CREATE INDEX `idx_produto_sances_raw_codigo` ON `produto_sances_raw` (`tenant_id`, `codigo`);

CREATE INDEX `idx_quantidade_sances_raw_pendente` ON `quantidade_sances_raw` (`tenant_id`, `processado_em`);

CREATE INDEX `idx_quantidade_sances_raw_produto` ON `quantidade_sances_raw` (`tenant_id`, `codigo_produto`);

CREATE INDEX `idx_endereco_sults_pessoa` ON `endereco_sults_raw` (`pessoa_id`);

CREATE INDEX `idx_empresa_sults_pessoa` ON `empresa_sults_raw` (`pessoa_id`);

ALTER TABLE `endereco_sults_raw` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_sults_raw` (`id`) ON DELETE CASCADE;

ALTER TABLE `empresa_sults_raw` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_sults_raw` (`id`) ON DELETE CASCADE;

ALTER TABLE `email_sances_raw` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_sances_raw` (`codigo_cliente`) ON DELETE CASCADE;

ALTER TABLE `endereco_sances_raw` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_sances_raw` (`codigo_cliente`) ON DELETE CASCADE;

ALTER TABLE `telefone_sances_raw` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_sances_raw` (`codigo_cliente`) ON DELETE CASCADE;

ALTER TABLE `pos_venda_peca_raw` ADD FOREIGN KEY (`codposv`) REFERENCES `pos_venda_raw` (`codigo`);

ALTER TABLE `pos_venda_servico_raw` ADD FOREIGN KEY (`codposv`) REFERENCES `pos_venda_raw` (`codigo`);

ALTER TABLE `pos_venda_nota_raw` ADD FOREIGN KEY (`codposv`) REFERENCES `pos_venda_raw` (`codigo`);

ALTER TABLE `pos_venda_parcela_raw` ADD FOREIGN KEY (`codposv`) REFERENCES `pos_venda_raw` (`codigo`);

ALTER TABLE `chamados_apoio_raw` ADD FOREIGN KEY (`chamado_codigo`) REFERENCES `chamados_raw` (`codigo`);

ALTER TABLE `chamados_etiqueta_raw` ADD FOREIGN KEY (`chamado_codigo`) REFERENCES `chamados_raw` (`codigo`);

CREATE TABLE IF NOT EXISTS `preco_sances_raw_produto_sances_raw` (
  `preco_sances_raw_codigo_produto` int,
  `produto_sances_raw_codigo` int,
  PRIMARY KEY (`preco_sances_raw_codigo_produto`, `produto_sances_raw_codigo`)
);

ALTER TABLE `preco_sances_raw_produto_sances_raw` ADD FOREIGN KEY (`preco_sances_raw_codigo_produto`) REFERENCES `preco_sances_raw` (`codigo_produto`);

ALTER TABLE `preco_sances_raw_produto_sances_raw` ADD FOREIGN KEY (`produto_sances_raw_codigo`) REFERENCES `produto_sances_raw` (`codigo`);


ALTER TABLE `quantidade_sances_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `produto_sances_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `preco_sances_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `modelo_veiculo_sances_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `financeiro_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `chamados_etiqueta_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `chamados_apoio_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `chamados_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `telemetria_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_peca_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_servico_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_nota_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_parcela_raw` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `recebimentos_raw` ADD FOREIGN KEY (`codigo_titulo`) REFERENCES `financeiro_raw` (`codigo`);
