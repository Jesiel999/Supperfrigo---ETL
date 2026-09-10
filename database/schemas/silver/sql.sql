CREATE TABLE IF NOT EXISTS `chamados_apoio_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `empresa_id` int,
  `chamado_codigo` int,
  `pessoa_id` int,
  `departamento_id` int,
  `pessoa_unidade` boolean
);

CREATE TABLE IF NOT EXISTS `chamados_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `codigo_raw` int NOT NULL,
  `titulo` text,
  `tipo` int,
  `situacao` int,
  `solicitante_id` int,
  `responsavel_id` int,
  `unidade_id` int,
  `departamento_id` int,
  `departamento_envio_id` int,
  `assunto_id` int,
  `data_aberto` datetime,
  `data_resolvido` datetime,
  `data_concluido` datetime,
  `data_resolver_planejado` datetime,
  `data_resolver_estipulado` datetime,
  `data_primeira_interacao` datetime,
  `data_ultima_alteracao` datetime,
  `avaliacao_nota` int,
  `avaliacao_observacao` text,
  `quantidade_interacao_publico` int,
  `quantidade_interacao_interno` int,
  `tempo_primeira_resposta` int,
  `tempo_resolucao` int,
  `sla_horas` decimal(10,2),
  `sla_cumprido` boolean,
  `horas_atrasado` decimal(10,2),
  `horas_resolver` decimal(10,2),
  `tipo_solicitacao` varchar(100),
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP),
  `atualizado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

CREATE TABLE IF NOT EXISTS `dim_departamento` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `empresa_id` int,
  `departamento_id` int,
  `nome` varchar(100)
);

CREATE TABLE IF NOT EXISTS `dim_etiqueta` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `etiqueta_id` int,
  `nome` varchar(255),
  `cor` varchar(20)
);

CREATE TABLE IF NOT EXISTS `chamados_etiqueta_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `empresa_id` int,
  `chamado_codigo` int,
  `etiqueta_id` int
);

CREATE TABLE IF NOT EXISTS `pessoa_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `id_sances` int,
  `id_sults` int,
  `id_multisys` int,
  `id_econnect` int,
  `cpf_cnpj` varchar(20),
  `nome` varchar(255),
  `sexo` varchar(1),
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP),
  `atualizado_em` datetime DEFAULT (CURRENT_TIMESTAMP),
  `id_nectar` int,
  `colaborador` boolean
);

CREATE TABLE IF NOT EXISTS `pos_venda_bi` (
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
  `codigo_cliente` bigint,
  `codigo_tipo_preco` bigint,
  `descricao_tipo_preco` varchar(255),
  `codigo_veiculo` bigint,
  `codigo_tipo_os` bigint,
  `km_entrada` decimal(15,2),
  `km_saida` decimal(15,2),
  `data_entrada` datetime,
  `data_saida` datetime,
  `solicitacao_cliente` text,
  `avaria` text,
  `defeito_averiguado` text,
  `codigo_proprietario` bigint,
  `codigo_tipo_midia` bigint,
  `descricao_tipo_midia` varchar(255),
  `codigo_modalidade_venda` bigint,
  `descricao_modalidade_venda` varchar(255),
  `codigo_conveniado` bigint,
  `codigo_consultor` bigint,
  `percentual_comissao_peca` decimal(10,4),
  `valor_comissao_peca_consultor` decimal(15,2),
  `percentual_comissao_servico` decimal(10,4),
  `valor_comissao_servico_consultor` decimal(15,2),
  `total_comissao_consultor` decimal(15,2),
  `codigo_usuario_insercao` bigint,
  `data_insercao` datetime,
  `codigo_usuario_alteracao` bigint,
  `data_alteracao` datetime,
  `codigo_usuario_cancelamento` bigint,
  `data_cancelamento` datetime,
  `codigo_usuario_fechamento` bigint,
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
  `margem_pecas` decimal(10,4),
  `margem_servicos` decimal(10,4),
  `margem_total` decimal(10,4),
  `ano` int,
  `mes` int,
  `mes_ano` varchar(7),
  `data_carga` datetime NOT NULL,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `condicao_pagamento` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `codigo` bigint NOT NULL,
  `descricao` varchar(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS `tipo_os` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `codigo` bigint NOT NULL,
  `descricao` varchar(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS `veiculo_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_sances` bigint,
  `codigo_econnect` bigint,
  `placa` varchar(20),
  `chassi` varchar(20),
  `codigo_modelo` bigint,
  `descricao_modelo` varchar(50),
  `codigo_cor` bigint,
  `descricao_cor` varchar(50),
  `ano_fabricacao` smallint,
  `ano_modelo` smallint
);

CREATE TABLE IF NOT EXISTS `pos_venda_peca_bi` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codigo_posvenda` bigint NOT NULL,
  `codigo_origem` bigint NOT NULL,
  `codigo_peca` bigint,
  `unidade_peca` varchar(30),
  `qtd_peca` decimal(15,4),
  `valor_unitario` decimal(15,4),
  `custo_unitario` decimal(15,4),
  `custo_total` decimal(15,2),
  `total_bruto` decimal(15,2),
  `valor_desconto` decimal(15,2),
  `total_liquido` decimal(15,2),
  `codigo_mecanico` bigint,
  `percentual_comissao_mecanico` decimal(10,4),
  `valor_comissao_mecanico` decimal(15,2),
  `peca_cancelada` boolean,
  `codigo_motivo_cancelamento` bigint,
  `data_carga` datetime NOT NULL,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `motivo_cancelamento` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `codigo` bigint NOT NULL,
  `descricao` varchar(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS `pos_venda_servico_bi` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codigo_posvenda` bigint NOT NULL,
  `codigo_origem` bigint NOT NULL,
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
  `servico_cancelado` boolean,
  `codigo_motivo_cancelamento` bigint,
  `data_carga` datetime NOT NULL,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `nota_bi` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codigo_posvenda` bigint NOT NULL,
  `codigo_origem` bigint NOT NULL,
  `tipo` varchar(20),
  `descricao` varchar(255),
  `codigo_nota` bigint,
  `numero_nota` bigint,
  `chave_nota` varchar(100),
  `data_faturamento` datetime,
  `operacao` varchar(255),
  `data_carga` datetime NOT NULL,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `pos_venda_parcela_bi` (
  `id` bigint AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo` bigint AUTO_INCREMENT,
  `codigo_posvenda` bigint NOT NULL,
  `codigo_origem` bigint NOT NULL,
  `tipo_parcela` enum(PECA,SERVICO,FRANQUIA),
  `ordem_parcela` varchar(20),
  `vencimento_parcela` date,
  `forma_cobranca_parcela` varchar(255),
  `valor_parcela` decimal(15,2),
  `data_carga` datetime NOT NULL,
  PRIMARY KEY (`id`, `codigo`)
);

CREATE TABLE IF NOT EXISTS `telemetria_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` bigint NOT NULL,
  `codigo_raw` bigint NOT NULL,
  `dispositivo_id` varchar(100),
  `veiculo_id` bigint NOT NULL,
  `data_evento` datetime(3) NOT NULL,
  `gsm_signal` int,
  `data_mode` int,
  `velocidade_kmh` decimal(10,2),
  `velocidade_roda_kmh` decimal(10,2),
  `tensao_externa_v` decimal(8,3),
  `tensao_bateria_v` decimal(8,3),
  `corrente_bateria` decimal(10,3),
  `gnss_status` boolean,
  `gnss_pdop` decimal(8,3),
  `gnss_hdop` decimal(8,3),
  `freio_acionado` boolean,
  `controle_cruzeiro_ativo` boolean,
  `embreagem_acionada` boolean,
  `pto_estado` int,
  `pedal_acelerador_pct` decimal(6,2),
  `carga_motor_pct` decimal(6,2),
  `combustivel_total_l` decimal(16,3),
  `nivel_combustivel_pct` decimal(6,2),
  `rotacao_motor_rpm` decimal(10,2),
  `diagnosticos_suportados` boolean,
  `requisicoes_suportadas` boolean,
  `indicacao_direcao` int,
  `desempenho_tacografo` int,
  `informacao_manuseio` int,
  `evento_sistema` int,
  `temperatura_liquido_arrefecimento_c` decimal(8,2),
  `taxa_combustivel_l_h` decimal(10,3),
  `economia_instantanea` decimal(10,3),
  `combustivel_total_alta_resolucao_l` decimal(16,3),
  `modo_sleep` boolean,
  `dados_validos` boolean NOT NULL DEFAULT true,
  `data_processamento` datetime(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3)),
  `criado_em` datetime(3) NOT NULL DEFAULT (CURRENT_TIMESTAMP(3))
);

CREATE TABLE IF NOT EXISTS `estoque_produto_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `descricao` varchar(255),
  `referencia` varchar(100),
  `referencia_fabrica` text,
  `codigo_ean` varchar(50),
  `codigo_barras` varchar(50),
  `sigla_unidade_medida` varchar(10),
  `descricao_unidade_medida` varchar(50),
  `codigo_categoria` int,
  `descricao_categoria` varchar(100),
  `descricao_grupo` varchar(100),
  `descricao_subgrupo` varchar(100),
  `endereco_setor` varchar(50),
  `endereco_rua` varchar(50),
  `endereco_andar` varchar(50),
  `ativo` tinyint,
  `data_processamento` datetime NOT NULL
);

CREATE TABLE IF NOT EXISTS `estoque_empresa_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_empresa` int NOT NULL,
  `cnpj` varchar(20),
  `nome_razao` varchar(255),
  `nome_fantasia` varchar(255),
  `apelido` varchar(100),
  `qtd_estoque` decimal(14,4) NOT NULL DEFAULT 0,
  `qtd_aplicadas` decimal(14,4) NOT NULL DEFAULT 0,
  `qtd_reservada` decimal(14,4) NOT NULL DEFAULT 0,
  `qtd_transito` decimal(14,4) NOT NULL DEFAULT 0,
  `qtd_pedido` decimal(14,4) NOT NULL DEFAULT 0,
  `qtd_bo` decimal(14,4) NOT NULL DEFAULT 0,
  `data_processamento` datetime NOT NULL
);

CREATE TABLE IF NOT EXISTS `estoque_modelo_veiculo_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_modelo` int NOT NULL,
  `descricao_modelo` varchar(255),
  `data_processamento` datetime NOT NULL
);

CREATE TABLE IF NOT EXISTS `estoque_precos_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_empresa` int NOT NULL,
  `cnpj` varchar(20),
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
  `data_processamento` datetime NOT NULL
);

CREATE TABLE IF NOT EXISTS `email_bi` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `pessoa_id` int NOT NULL,
  `email` varchar(500)
);

CREATE TABLE IF NOT EXISTS `endereco_bi` (
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

CREATE TABLE IF NOT EXISTS `empresa_bi` (
  `codigo_empresa` int PRIMARY KEY,
  `nome_empresa` varchar(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS `tenant` (
  `id` int PRIMARY KEY AUTO_INCREMENT,
  `nome` varchar(120) NOT NULL,
  `slug` varchar(60) NOT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT '1'
);

CREATE TABLE IF NOT EXISTS `financeiro_bi` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_raw` int UNIQUE NOT NULL,
  `id_empresa` varchar(50),
  `id_pessoa` varchar(50),
  `tipo_titulo` varchar(20),
  `numero_documento` varchar(100),
  `ordem` varchar(50),
  `origem` varchar(100),
  `codigo_situacao` varchar(50),
  `descricao_situacao` varchar(255),
  `status_financeiro` varchar(50),
  `descricao_forma_cobranca` varchar(255),
  `descricao_forma_pagamento` varchar(255),
  `codigo_categoria_financeira` varchar(50),
  `descricao_categoria_financeira` varchar(255),
  `codigo_centro_custo` varchar(50),
  `descricao_centro_custo` varchar(255),
  `codigo_conta_resultado` varchar(50),
  `descricao_conta_resultado` varchar(255),
  `data_emissao` date,
  `data_competencia` date,
  `data_vencimento` date,
  `data_baixa` date,
  `data_cancelamento` date,
  `valor_nominal` decimal(15,2),
  `valor_multa` decimal(15,2),
  `acrescimo` decimal(15,2),
  `valor_total` decimal(15,2),
  `dias_atraso` int,
  `dias_pagamento` int,
  `dias_recebimento` int,
  `criado_em` datetime DEFAULT (CURRENT_TIMESTAMP),
  `atualizado_em` datetime DEFAULT (CURRENT_TIMESTAMP)
);

  CREATE TABLE IF NOT EXISTS `recebimentos_bi` (
    `id` int PRIMARY KEY AUTO_INCREMENT,
    `tenant_id` int,
    `codigo_raw` bigint,
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

CREATE UNIQUE INDEX `uk_chamado` ON `chamados_bi` (`codigo_raw`);

CREATE UNIQUE INDEX `uk_departamento` ON `dim_departamento` (`empresa_id`, `departamento_id`);

CREATE UNIQUE INDEX `uk_etiqueta` ON `dim_etiqueta` (`etiqueta_id`);

CREATE UNIQUE INDEX `uk_pessoa_bi_cpf_cnpj` ON `pessoa_bi` (`cpf_cnpj`);

CREATE INDEX `idx_nome` ON `pessoa_bi` (`nome`);

CREATE INDEX `idx_cpf` ON `pessoa_bi` (`id_sances`, `id_sults`);

CREATE UNIQUE INDEX `pos_venda_bi_index_6` ON `pos_venda_bi` (`codigo_origem`);

CREATE INDEX `pos_venda_bi_index_7` ON `pos_venda_bi` (`data_insercao`);

CREATE INDEX `pos_venda_bi_index_8` ON `pos_venda_bi` (`data_alteracao`);

CREATE INDEX `pos_venda_bi_index_9` ON `pos_venda_bi` (`data_fechamento`);

CREATE INDEX `pos_venda_bi_index_10` ON `pos_venda_bi` (`codigo_empresa`);

CREATE INDEX `pos_venda_bi_index_11` ON `pos_venda_bi` (`codigo_cliente`);

CREATE INDEX `pos_venda_bi_index_12` ON `pos_venda_bi` (`codigo_consultor`);

CREATE INDEX `pos_venda_bi_index_13` ON `pos_venda_bi` (`codigo_situacao`);

CREATE INDEX `pos_venda_bi_index_14` ON `pos_venda_bi` (`numero`);

CREATE INDEX `pos_venda_bi_index_15` ON `pos_venda_bi` (`ano`, `mes`);

CREATE INDEX `pos_venda_peca_bi_index_16` ON `pos_venda_peca_bi` (`codigo_posvenda`);

CREATE INDEX `pos_venda_peca_bi_index_17` ON `pos_venda_peca_bi` (`codigo_origem`);

CREATE INDEX `pos_venda_peca_bi_index_18` ON `pos_venda_peca_bi` (`codigo_peca`);

CREATE INDEX `pos_venda_servico_bi_index_19` ON `pos_venda_servico_bi` (`codigo_posvenda`);

CREATE INDEX `pos_venda_servico_bi_index_20` ON `pos_venda_servico_bi` (`codigo_origem`);

CREATE INDEX `pos_venda_servico_bi_index_21` ON `pos_venda_servico_bi` (`codigo_servico`);

CREATE INDEX `nota_bi_index_22` ON `nota_bi` (`codigo_posvenda`);

CREATE INDEX `nota_bi_index_23` ON `nota_bi` (`codigo_nota`);

CREATE INDEX `nota_bi_index_24` ON `nota_bi` (`numero_nota`);

CREATE INDEX `nota_bi_index_25` ON `nota_bi` (`data_faturamento`);

CREATE INDEX `pos_venda_parcela_bi_index_26` ON `pos_venda_parcela_bi` (`codigo_posvenda`);

CREATE INDEX `pos_venda_parcela_bi_index_27` ON `pos_venda_parcela_bi` (`codigo_origem`);

CREATE INDEX `pos_venda_parcela_bi_index_28` ON `pos_venda_parcela_bi` (`tipo_parcela`);

CREATE INDEX `pos_venda_parcela_bi_index_29` ON `pos_venda_parcela_bi` (`vencimento_parcela`);

CREATE UNIQUE INDEX `uk_telemetria_bronze` ON `telemetria_bi` (`codigo_raw`);

CREATE INDEX `idx_telemetria_tenant_data` ON `telemetria_bi` (`tenant_id`, `data_evento`);

CREATE INDEX `idx_telemetria_veiculo_data` ON `telemetria_bi` (`tenant_id`, `veiculo_id`, `data_evento`);

CREATE UNIQUE INDEX `uk_estoque_produto_tenant_codigo` ON `estoque_produto_bi` (`tenant_id`, `codigo_produto`);

CREATE INDEX `idx_produto_ultimo` ON `estoque_produto_bi` (`tenant_id`, `codigo_produto`, `data_processamento`);

CREATE UNIQUE INDEX `uk_estoque_empresa_tenant_produto_empresa` ON `estoque_empresa_bi` (`tenant_id`, `codigo_produto`, `codigo_empresa`);

CREATE INDEX `idx_empresa_produto_data` ON `estoque_empresa_bi` (`tenant_id`, `codigo_produto`, `codigo_empresa`, `data_processamento`);

CREATE UNIQUE INDEX `uk_estoque_modelo_tenant_produto_modelo` ON `estoque_modelo_veiculo_bi` (`tenant_id`, `codigo_produto`, `codigo_modelo`);

CREATE UNIQUE INDEX `uk_estoque_precos_tenant_produto_empresa` ON `estoque_precos_bi` (`tenant_id`, `codigo_produto`, `codigo_empresa`);

CREATE INDEX `idx_email_bi_pessoa` ON `email_bi` (`pessoa_id`);

CREATE INDEX `idx_endereco_bi_pessoa` ON `endereco_bi` (`pessoa_id`);

CREATE INDEX `idx_id_empresa` ON `financeiro_bi` (`id_empresa`);

CREATE INDEX `idx_id_pessoa` ON `financeiro_bi` (`id_pessoa`);

CREATE INDEX `idx_tipo_titulo` ON `financeiro_bi` (`tipo_titulo`);

CREATE INDEX `idx_status_financeiro` ON `financeiro_bi` (`status_financeiro`);

CREATE INDEX `idx_data_vencimento` ON `financeiro_bi` (`data_vencimento`);

CREATE INDEX `idx_data_baixa` ON `financeiro_bi` (`data_baixa`);

ALTER TABLE `estoque_empresa_bi` ADD FOREIGN KEY (`tenant_id`, `codigo_produto`) REFERENCES `estoque_produto_bi` (`tenant_id`, `codigo_produto`) ON DELETE CASCADE;

ALTER TABLE `estoque_modelo_veiculo_bi` ADD FOREIGN KEY (`tenant_id`, `codigo_produto`) REFERENCES `estoque_produto_bi` (`tenant_id`, `codigo_produto`) ON DELETE CASCADE;

ALTER TABLE `estoque_precos_bi` ADD FOREIGN KEY (`tenant_id`, `codigo_produto`) REFERENCES `estoque_produto_bi` (`tenant_id`, `codigo_produto`) ON DELETE CASCADE;

ALTER TABLE `email_bi` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_bi` (`id`) ON DELETE CASCADE;

ALTER TABLE `endereco_bi` ADD FOREIGN KEY (`pessoa_id`) REFERENCES `pessoa_bi` (`id`) ON DELETE CASCADE;

ALTER TABLE `pos_venda_peca_bi` ADD FOREIGN KEY (`codigo_posvenda`) REFERENCES `pos_venda_bi` (`codigo`);

ALTER TABLE `pos_venda_servico_bi` ADD FOREIGN KEY (`codigo_posvenda`) REFERENCES `pos_venda_bi` (`codigo`);

ALTER TABLE `nota_bi` ADD FOREIGN KEY (`codigo_posvenda`) REFERENCES `pos_venda_bi` (`codigo`);

ALTER TABLE `pos_venda_parcela_bi` ADD FOREIGN KEY (`codigo_posvenda`) REFERENCES `pos_venda_bi` (`codigo`);

ALTER TABLE `chamados_bi` ADD FOREIGN KEY (`departamento_id`) REFERENCES `dim_departamento` (`departamento_id`);

ALTER TABLE `chamados_apoio_bi` ADD FOREIGN KEY (`departamento_id`) REFERENCES `dim_departamento` (`departamento_id`);

ALTER TABLE `chamados_etiqueta_bi` ADD FOREIGN KEY (`etiqueta_id`) REFERENCES `dim_etiqueta` (`etiqueta_id`);

CREATE TABLE IF NOT EXISTS `pessoa_bi_chamados_bi` (
  `pessoa_bi_id_sults` int,
  `chamados_bi_solicitante_id` int,
  PRIMARY KEY (`pessoa_bi_id_sults`, `chamados_bi_solicitante_id`)
);

ALTER TABLE `pessoa_bi_chamados_bi` ADD FOREIGN KEY (`pessoa_bi_id_sults`) REFERENCES `pessoa_bi` (`id_sults`);

ALTER TABLE `pessoa_bi_chamados_bi` ADD FOREIGN KEY (`chamados_bi_solicitante_id`) REFERENCES `chamados_bi` (`solicitante_id`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_chamados_bi(1)` (
  `pessoa_bi_id_sults` int,
  `chamados_bi_responsavel_id` int,
  PRIMARY KEY (`pessoa_bi_id_sults`, `chamados_bi_responsavel_id`)
);

ALTER TABLE `pessoa_bi_chamados_bi(1)` ADD FOREIGN KEY (`pessoa_bi_id_sults`) REFERENCES `pessoa_bi` (`id_sults`);

ALTER TABLE `pessoa_bi_chamados_bi(1)` ADD FOREIGN KEY (`chamados_bi_responsavel_id`) REFERENCES `chamados_bi` (`responsavel_id`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_chamados_apoio_bi` (
  `pessoa_bi_id_sults` int,
  `chamados_apoio_bi_pessoa_id` int,
  PRIMARY KEY (`pessoa_bi_id_sults`, `chamados_apoio_bi_pessoa_id`)
);

ALTER TABLE `pessoa_bi_chamados_apoio_bi` ADD FOREIGN KEY (`pessoa_bi_id_sults`) REFERENCES `pessoa_bi` (`id_sults`);

ALTER TABLE `pessoa_bi_chamados_apoio_bi` ADD FOREIGN KEY (`chamados_apoio_bi_pessoa_id`) REFERENCES `chamados_apoio_bi` (`pessoa_id`);


ALTER TABLE `pos_venda_bi` ADD FOREIGN KEY (`codigo_veiculo`) REFERENCES `veiculo_bi` (`codigo_sances`);

CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_consultor` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_consultor`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi` ADD FOREIGN KEY (`pos_venda_bi_codigo_consultor`) REFERENCES `pos_venda_bi` (`codigo_consultor`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(1)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_usuario_insercao` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_usuario_insercao`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(1)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(1)` ADD FOREIGN KEY (`pos_venda_bi_codigo_usuario_insercao`) REFERENCES `pos_venda_bi` (`codigo_usuario_insercao`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(2)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_usuario_alteracao` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_usuario_alteracao`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(2)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(2)` ADD FOREIGN KEY (`pos_venda_bi_codigo_usuario_alteracao`) REFERENCES `pos_venda_bi` (`codigo_usuario_alteracao`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(3)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_usuario_fechamento` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_usuario_fechamento`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(3)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(3)` ADD FOREIGN KEY (`pos_venda_bi_codigo_usuario_fechamento`) REFERENCES `pos_venda_bi` (`codigo_usuario_fechamento`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(4)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_usuario_cancelamento` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_usuario_cancelamento`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(4)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(4)` ADD FOREIGN KEY (`pos_venda_bi_codigo_usuario_cancelamento`) REFERENCES `pos_venda_bi` (`codigo_usuario_cancelamento`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(5)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_cliente` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_cliente`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(5)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(5)` ADD FOREIGN KEY (`pos_venda_bi_codigo_cliente`) REFERENCES `pos_venda_bi` (`codigo_cliente`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(6)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_empresa` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_empresa`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(6)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(6)` ADD FOREIGN KEY (`pos_venda_bi_codigo_empresa`) REFERENCES `pos_venda_bi` (`codigo_empresa`);


CREATE TABLE IF NOT EXISTS `pessoa_bi_pos_venda_bi(7)` (
  `pessoa_bi_id_sances` int,
  `pos_venda_bi_codigo_proprietario` bigint,
  PRIMARY KEY (`pessoa_bi_id_sances`, `pos_venda_bi_codigo_proprietario`)
);

ALTER TABLE `pessoa_bi_pos_venda_bi(7)` ADD FOREIGN KEY (`pessoa_bi_id_sances`) REFERENCES `pessoa_bi` (`id_sances`);

ALTER TABLE `pessoa_bi_pos_venda_bi(7)` ADD FOREIGN KEY (`pos_venda_bi_codigo_proprietario`) REFERENCES `pos_venda_bi` (`codigo_proprietario`);


CREATE TABLE IF NOT EXISTS `chamados_bi_chamados_etiqueta_bi` (
  `chamados_bi_codigo_raw` int,
  `chamados_etiqueta_bi_chamado_codigo` int,
  PRIMARY KEY (`chamados_bi_codigo_raw`, `chamados_etiqueta_bi_chamado_codigo`)
);

ALTER TABLE `chamados_bi_chamados_etiqueta_bi` ADD FOREIGN KEY (`chamados_bi_codigo_raw`) REFERENCES `chamados_bi` (`codigo_raw`);

ALTER TABLE `chamados_bi_chamados_etiqueta_bi` ADD FOREIGN KEY (`chamados_etiqueta_bi_chamado_codigo`) REFERENCES `chamados_etiqueta_bi` (`chamado_codigo`);


CREATE TABLE IF NOT EXISTS `chamados_bi_chamados_apoio_bi` (
  `chamados_bi_codigo_raw` int,
  `chamados_apoio_bi_chamado_codigo` int,
  PRIMARY KEY (`chamados_bi_codigo_raw`, `chamados_apoio_bi_chamado_codigo`)
);

ALTER TABLE `chamados_bi_chamados_apoio_bi` ADD FOREIGN KEY (`chamados_bi_codigo_raw`) REFERENCES `chamados_bi` (`codigo_raw`);

ALTER TABLE `chamados_bi_chamados_apoio_bi` ADD FOREIGN KEY (`chamados_apoio_bi_chamado_codigo`) REFERENCES `chamados_apoio_bi` (`chamado_codigo`);


CREATE TABLE IF NOT EXISTS `veiculo_bi_telemetria_bi` (
  `veiculo_bi_codigo_econnect` bigint,
  `telemetria_bi_veiculo_id` bigint,
  PRIMARY KEY (`veiculo_bi_codigo_econnect`, `telemetria_bi_veiculo_id`)
);

ALTER TABLE `veiculo_bi_telemetria_bi` ADD FOREIGN KEY (`veiculo_bi_codigo_econnect`) REFERENCES `veiculo_bi` (`codigo_econnect`);

ALTER TABLE `veiculo_bi_telemetria_bi` ADD FOREIGN KEY (`telemetria_bi_veiculo_id`) REFERENCES `telemetria_bi` (`veiculo_id`);


CREATE TABLE IF NOT EXISTS `motivo_cancelamento_pos_venda_peca_bi` (
  `motivo_cancelamento_codigo` bigint,
  `pos_venda_peca_bi_codigo_motivo_cancelamento` bigint,
  PRIMARY KEY (`motivo_cancelamento_codigo`, `pos_venda_peca_bi_codigo_motivo_cancelamento`)
);

ALTER TABLE `motivo_cancelamento_pos_venda_peca_bi` ADD FOREIGN KEY (`motivo_cancelamento_codigo`) REFERENCES `motivo_cancelamento` (`codigo`);

ALTER TABLE `motivo_cancelamento_pos_venda_peca_bi` ADD FOREIGN KEY (`pos_venda_peca_bi_codigo_motivo_cancelamento`) REFERENCES `pos_venda_peca_bi` (`codigo_motivo_cancelamento`);


CREATE TABLE IF NOT EXISTS `motivo_cancelamento_pos_venda_servico_bi` (
  `motivo_cancelamento_codigo` bigint,
  `pos_venda_servico_bi_codigo_motivo_cancelamento` bigint,
  PRIMARY KEY (`motivo_cancelamento_codigo`, `pos_venda_servico_bi_codigo_motivo_cancelamento`)
);

ALTER TABLE `motivo_cancelamento_pos_venda_servico_bi` ADD FOREIGN KEY (`motivo_cancelamento_codigo`) REFERENCES `motivo_cancelamento` (`codigo`);

ALTER TABLE `motivo_cancelamento_pos_venda_servico_bi` ADD FOREIGN KEY (`pos_venda_servico_bi_codigo_motivo_cancelamento`) REFERENCES `pos_venda_servico_bi` (`codigo_motivo_cancelamento`);


CREATE TABLE IF NOT EXISTS `pos_venda_bi_condicao_pagamento` (
  `pos_venda_bi_codigo_condicao_pagamento` bigint,
  `condicao_pagamento_codigo` bigint,
  PRIMARY KEY (`pos_venda_bi_codigo_condicao_pagamento`, `condicao_pagamento_codigo`)
);

ALTER TABLE `pos_venda_bi_condicao_pagamento` ADD FOREIGN KEY (`pos_venda_bi_codigo_condicao_pagamento`) REFERENCES `pos_venda_bi` (`codigo_condicao_pagamento`);

ALTER TABLE `pos_venda_bi_condicao_pagamento` ADD FOREIGN KEY (`condicao_pagamento_codigo`) REFERENCES `condicao_pagamento` (`codigo`);


CREATE TABLE IF NOT EXISTS `pos_venda_bi_tipo_os` (
  `pos_venda_bi_codigo_tipo_os` bigint,
  `tipo_os_codigo` bigint,
  PRIMARY KEY (`pos_venda_bi_codigo_tipo_os`, `tipo_os_codigo`)
);

ALTER TABLE `pos_venda_bi_tipo_os` ADD FOREIGN KEY (`pos_venda_bi_codigo_tipo_os`) REFERENCES `pos_venda_bi` (`codigo_tipo_os`);

ALTER TABLE `pos_venda_bi_tipo_os` ADD FOREIGN KEY (`tipo_os_codigo`) REFERENCES `tipo_os` (`codigo`);


ALTER TABLE `financeiro_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `estoque_empresa_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `estoque_modelo_veiculo_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `estoque_precos_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `estoque_produto_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `nota_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_servico_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `telemetria_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `veiculo_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_parcela_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `pos_venda_peca_bi` ADD FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`);

ALTER TABLE `recebimentos_bi` ADD FOREIGN KEY (`codigo_raw`) REFERENCES `financeiro_bi` (`codigo_raw`);
