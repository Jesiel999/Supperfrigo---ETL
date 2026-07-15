-- ── MODULO ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `modulo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `aplicacao_id` int NOT NULL,
  `nome` varchar(80) NOT NULL,
  `codigo` varchar(60) NOT NULL,
  `rota` varchar(160) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_modulo` (`aplicacao_id`,`codigo`),
  CONSTRAINT `modulo_ibfk_1` FOREIGN KEY (`aplicacao_id`) REFERENCES `aplicacao` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
