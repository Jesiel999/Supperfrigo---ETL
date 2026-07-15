-- ── USUARIO_EMPRESA ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS `usuario_empresa` (
  `usuario_id` int NOT NULL,
  `tenant_id` int NOT NULL,
  `codigo_empresa` int NOT NULL,
  PRIMARY KEY (`usuario_id`,`tenant_id`,`codigo_empresa`),
  KEY `tenant_id` (`tenant_id`),
  CONSTRAINT `usuario_empresa_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `usuario_empresa_ibfk_2` FOREIGN KEY (`tenant_id`) REFERENCES `tenant` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
