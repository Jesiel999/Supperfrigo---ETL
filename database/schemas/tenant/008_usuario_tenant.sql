-- ── USUARIO_TENANT ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `usuario_tenant` (
  `usuario_id` int NOT NULL,
  `tenant_id` int NOT NULL,
  `perfil_id` int NOT NULL,
  `ativo` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`usuario_id`,`tenant_id`),
  KEY `tenant_id` (`tenant_id`),
  KEY `perfil_id` (`perfil_id`),
  CONSTRAINT `usuario_tenant_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `usuario_tenant_ibfk_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`) ON DELETE CASCADE,
  CONSTRAINT `usuario_tenant_ibfk_3` FOREIGN KEY (`perfil_id`) REFERENCES `perfil` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
