CREATE TABLE IF NOT EXISTS `pipeline_offset` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tenant_id` int NOT NULL,
  `origem` varchar(50) NOT NULL,
  `offset_atual` int NOT NULL DEFAULT '1',
  `atualizado_em` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `endpoint` varchar(1000) DEFAULT NULL,
  `status` varchar(45) DEFAULT NULL,
  `ultima_execucao` datetime DEFAULT NULL,
  `ultimo_sucesso` datetime DEFAULT NULL,
  `ultimo_erro` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_pipeline_offset_tenant_origem` (`tenant_id`,`origem`),
  KEY `idx_offset_ultima` (`origem`,`tenant_id`,`ultima_execucao`),
  CONSTRAINT `pipeline_ibfk_1` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73623 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci