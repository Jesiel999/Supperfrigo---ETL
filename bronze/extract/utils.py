from datetime import datetime


def normalizar(valor) -> str:
    if valor is None:
        return ""
    valor = str(valor).strip().replace("T", " ")
    if "+" in valor:
        valor = valor.split("+")[0]
    if "Z" in valor:
        valor = valor.replace("Z", "")
    if "." in valor:
        valor = valor.split(".")[0]
    return valor.strip()


def converter_data(data_str) -> str | None:
    if not data_str:
        return None
    try:
        data_str = str(data_str).strip().replace("Z", "").replace("T", " ")
        if "+" in data_str:
            data_str = data_str.split("+")[0]
        if "." in data_str:
            data_str = data_str.split(".")[0]
        data_str = data_str.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(data_str, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return None
    except Exception:
        return None


def normalizar_cpf_cnpj(valor) -> str:
    """Mantém somente dígitos — usado como chave de match entre Sances e Sults."""
    if not valor:
        return ""
    return "".join(ch for ch in str(valor) if ch.isdigit())
