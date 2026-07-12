-- ==========================================================
--  MULTI-TENANT SCHEMA
--  Ordem: TENANT → APLICACAO → MODULO → PERMISSAO
--         → PERFIL → USUARIO → relacionamentos
-- ==========================================================

-- ── TENANT ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tenant (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    nome       VARCHAR(120) NOT NULL,
    slug       VARCHAR(60)  NOT NULL UNIQUE,   -- ex: "giiro-apg"
    ativo      TINYINT(1)   NOT NULL DEFAULT 1,
    criado_em  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_slug (slug)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── APLICACAO ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aplicacao (
    id    INT AUTO_INCREMENT PRIMARY KEY,
    nome  VARCHAR(80) NOT NULL UNIQUE,         -- "Financeiro", "OKRs", "CRM"
    slug  VARCHAR(60) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── MODULO ────────────────────────────────────────────────
-- Cada aplicação tem módulos (ex: Financeiro → inadimplencia, dre, pmp...)
CREATE TABLE IF NOT EXISTS modulo (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    aplicacao_id  INT          NOT NULL,
    nome          VARCHAR(80)  NOT NULL,
    codigo        VARCHAR(60)  NOT NULL,       -- ex: "inadimplencia"
    rota          VARCHAR(160),
    UNIQUE KEY uk_modulo (aplicacao_id, codigo),
    FOREIGN KEY (aplicacao_id) REFERENCES aplicacao(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── PERMISSAO ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS permissao (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    modulo_id  INT         NOT NULL,
    codigo     VARCHAR(60) NOT NULL,           -- "visualizar","criar","editar","excluir"
    descricao  VARCHAR(120),
    UNIQUE KEY uk_perm (modulo_id, codigo),
    FOREIGN KEY (modulo_id) REFERENCES modulo(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── PERFIL ────────────────────────────────────────────────
-- Perfil pertence ao tenant (cada tenant tem seus próprios perfil)
CREATE TABLE IF NOT EXISTS perfil (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id  INT          NOT NULL,
    nome       VARCHAR(80)  NOT NULL,          -- "Administrador", "Gestor"...
    descricao  VARCHAR(200),
    cor        VARCHAR(10)  DEFAULT '#64748b',
    ativo      TINYINT(1)   NOT NULL DEFAULT 1,
    is_admin      TINYINT(1)   NOT NULL DEFAULT 0,
    UNIQUE KEY uk_perfil (tenant_id, nome),
    FOREIGN KEY (tenant_id) REFERENCES tenant(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── PERFIL_PERMISSAO ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS perfil_permissao (
    perfil_id    INT NOT NULL,
    permissao_id INT NOT NULL,
    PRIMARY KEY (perfil_id, permissao_id),
    FOREIGN KEY (perfil_id)    REFERENCES perfil(id)    ON DELETE CASCADE,
    FOREIGN KEY (permissao_id) REFERENCES permissao(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── USUARIO ───────────────────────────────────────────────
-- Usuário existe independente de tenant (pode ser multi-tenant)
CREATE TABLE IF NOT EXISTS usuarios (
    id                INT  NOT NULL PRIMARY KEY DEFAULT (UUID()),
    username          VARCHAR(80)  NOT NULL UNIQUE,
    nome              VARCHAR(120) NOT NULL,
    email             VARCHAR(120) NOT NULL UNIQUE,
    telefone          VARCHAR(36),
    hashed_password       VARCHAR(255) NOT NULL,
    perfil_id           INT NOT NULL,
    ativo             TINYINT(1)   NOT NULL DEFAULT 1,
    criado_em         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultimo_acesso     DATETIME,
    INDEX idx_username (username),
    INDEX idx_email    (email)
    FOREIGN KEY (perfil_id) REFERENCES perfil(id),
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ── USUARIO_TENANT ────────────────────────────────────────
-- Relacionamento N:N — um usuário pode pertencer a vários tenants
-- com perfil diferentes em cada um
CREATE TABLE usuario_tenant (
    usuario_id  INT         NOT NULL,
    tenant_id   INT         NOT NULL,
    perfil_id   INT         NOT NULL,   -- espelha usuarios.perfil_id (sincronizado pela API)
    ativo       TINYINT(1)  NOT NULL DEFAULT 1,
    PRIMARY KEY (usuario_id, tenant_id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id)  REFERENCES tenant(id)    ON DELETE CASCADE,
    FOREIGN KEY (perfil_id)  REFERENCES perfil(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
-- ── USUARIO_EMPRESA ───────────────────────────────────────
-- Controla quais empresas (codigo_empresa da API) cada usuário pode ver
-- dentro de um tenant. Vazio = acesso a todas as empresas do tenant.
CREATE TABLE usuario_empresa (
    usuario_id     INT NOT NULL,
    tenant_id      INT NOT NULL,
    codigo_empresa INT NOT NULL,
    PRIMARY KEY (usuario_id, tenant_id, codigo_empresa),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id)  REFERENCES tenant(id)   ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
-- ==========================================================
--  DADOS INICIAIS
-- ==========================================================

-- Aplicações
INSERT IGNORE INTO aplicacao (nome, slug) VALUES
    ('Financeiro', 'financeiro'),
    ('OKRs',       'okrs'),
    ('CONFIG',        'config');

-- Módulos do Financeiro
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Inadimplência', 'inadimplencia' FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'DRE',                     'dre'           FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'PMP',                     'pmp'           FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Contas a Receber',        'contas_receber'          FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Contas a Pagar',          'contas_pagar'            FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Cobranças',               'cobrancas'               FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Fluxo de Caixa',          'fluxo_caixa'             FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Aging Report',            'aging_report'            FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Relatórios',              'relatorios'              FROM aplicacao WHERE slug = 'financeiro';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Usuários',          'usuarios'          FROM aplicacao WHERE slug = 'config';
INSERT IGNORE INTO modulo (aplicacao_id, nome, codigo)
SELECT id, 'Permissões',        'permissoes'        FROM aplicacao WHERE slug = 'config';

-- Permissões padrão para cada módulo
INSERT IGNORE INTO permissao (modulo_id, codigo, descricao)
SELECT m.id, p.codigo, p.descricao
FROM modulo m
CROSS JOIN (
    SELECT 'visualizar' codigo, 'Pode visualizar'  descricao UNION ALL
    SELECT 'criar',             'Pode criar'                  UNION ALL
    SELECT 'editar',            'Pode editar'                 UNION ALL
    SELECT 'excluir',           'Pode excluir'
) p
WHERE m.aplicacao_id = (SELECT id FROM aplicacao WHERE slug = 'financeiro');
