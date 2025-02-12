from pydantic import BaseModel
from typing import List

class Pedido(BaseModel):
    numero: int
    cod_pedidov: int
    nome_cliente: str
    vendedor: str
    transportadora: str

class Conferencia(BaseModel):
    prefaturamento: int
    produto: str
    cor: str
    tamanho: str
    quantidade: int
    ptc: str
