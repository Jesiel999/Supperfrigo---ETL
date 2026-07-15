-- ── APLICACAO ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `aplicacao` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(80) NOT NULL,
  `slug` varchar(60) NOT NULL,
  `sistema_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`),
  UNIQUE KEY `slug` (`slug`),
  KEY `sistema_ibfk_1` (`sistema_id`),
  CONSTRAINT `sistema_ibfk_1` FOREIGN KEY (`sistema_id`) REFERENCES `sistemas` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
