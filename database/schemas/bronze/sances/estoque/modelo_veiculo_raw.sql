CREATE TABLE IF NOT EXISTS `modelo_veiculo_sances_raw` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `pipeline` varchar(50) COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'estoque_sances',
  `offset_pagina` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_modelo` int DEFAULT NULL,
  `descricao_modelo` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `data_extracao` datetime NOT NULL,
  `processado_em` datetime DEFAULT NULL,
  `criado_em` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_modelo_veiculo_sances_raw_pendente` (`tenant_id`,`pipeline`,`processado_em`),
  KEY `idx_modelo_veiculo_sances_raw_produto` (`tenant_id`,`codigo_produto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci