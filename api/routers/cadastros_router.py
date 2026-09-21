from api.routers.cadastros_simples_router import criar_router_cadastro_simples

router_marcas = criar_router_cadastro_simples(
    "marca", "/api/marcas", "Marcas", "marca"
)
router_modelos = criar_router_cadastro_simples(
    "modelo", "/api/modelos", "Modelos", "modelo"
)
router_toners = criar_router_cadastro_simples(
    "toner", "/api/toners", "Toners", "toner"
)
router_departamentos = criar_router_cadastro_simples(
    "dim_departamento", "/api/departamentos", "Departamentos", "departamento"
)
