CREATE TABLE IF NOT EXISTS `estoque_modelo_veiculo_bi` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `codigo_produto` int NOT NULL,
  `codigo_modelo` int NOT NULL,
  `descricao_modelo` varchar(255) COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `data_processamento` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_estoque_modelo_tenant_produto_modelo` (`tenant_id`,`codigo_produto`,`codigo_modelo`),
  CONSTRAINT `fk_estoque_modelo_produto` FOREIGN KEY (`tenant_id`, `codigo_produto`) REFERENCES `estoque_produto_bi` (`tenant_id`, `codigo_produto`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;