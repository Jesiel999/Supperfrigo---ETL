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
