import requests

url = "https://api.sancesturbo.com.br/integracao/cadastros/pessoa"

headers = {
    "Authorization": f"Bearer {'MzM1NTEy.4d0YGzMOYeVqT971eO2hfNGD1Rjsa9qt8kw_mgifOcLOCTrbS_nzKMmN-WRz'}"
}

response = requests.get(
    url,
    headers=headers,
    params={
        "cpf_cnpj": "",
        "codigo_cliente": "4"
    }
)

print(response.status_code)
print(response.text)