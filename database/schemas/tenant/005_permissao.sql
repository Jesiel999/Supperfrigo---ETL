-- ── PERMISSAO ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `permissao` (
  `id` int NOT NULL AUTO_INCREMENT,
  `modulo_id` int NOT NULL,
  `codigo` varchar(60) NOT NULL,
  `descricao` varchar(120) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_perm` (`modulo_id`,`codigo`),
  CONSTRAINT `permissao_ibfk_1` FOREIGN KEY (`modulo_id`) REFERENCES `modulo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
