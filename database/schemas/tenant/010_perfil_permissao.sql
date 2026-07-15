-- ── PERFIL_PERMISSAO ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS `perfil_permissao` (
  `perfil_id` int NOT NULL,
  `permissao_id` int NOT NULL,
  PRIMARY KEY (`perfil_id`,`permissao_id`),
  KEY `permissao_id` (`permissao_id`),
  CONSTRAINT `perfil_permissao_ibfk_1` FOREIGN KEY (`perfil_id`) REFERENCES `perfil` (`id`) ON DELETE CASCADE,
  CONSTRAINT `perfil_permissao_ibfk_2` FOREIGN KEY (`permissao_id`) REFERENCES `permissao` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
