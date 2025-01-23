import pandas as pd
import fdb
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.simpledialog import askstring


# Função para consultar o estoque de um produto no Firebird e obter o nome da cor
def consultar_estoque(cursor, cod_produto, cod_cor, tamanho, filiais):
    try:
        query_estoque = f"""
        SELECT SUM(saldo) AS QUANTIDADE_EM_ESTOQUE,
               (SELECT descricao FROM CORES WHERE cod_cor = '{cod_cor}') AS NOME_COR
        FROM ESTOQUES_LOCAIS
        WHERE PRODUTO = (SELECT produto FROM PRODUTOS WHERE cod_produto = '{cod_produto}')
        AND COR = (SELECT cor FROM CORES WHERE cod_cor = '{cod_cor}')
        AND TAMANHO = '{tamanho}'
        AND Estampa = '0'
        AND filial IN ({filiais})
        """
        cursor.execute(query_estoque)
        result = cursor.fetchone()
        quantidade_estoque = result[0] if result[0] is not None else 0
        nome_cor = result[1] if result[1] is not None else 'Desconhecida'
        return quantidade_estoque, nome_cor
    except fdb.DatabaseError as e:
        print(f"Erro ao executar consulta SQL: {e}")
        return None, None


# Configurar conexão com o banco de dados Firebird
con = fdb.connect(
    dsn='milleniumflexmetal.ddns.net:c:/sys/base/millennium',
    user='SYSDBA',
    password='masterkey',
    charset='UTF8'
)
cursor = con.cursor()

# Selecionar o arquivo Excel
Tk().withdraw()
arquivo_excel = askopenfilename(title="Selecione a planilha de resumo", filetypes=[("Excel files", "*.xlsm")])

# Perguntar ao usuário quais filiais ele quer consultar
filiais = askstring("Selecionar Filiais",
                    "Digite os números das filiais separados por vírgulas (2 - Flexmetal, 14 - Orlando, 19 - Megatoon RS):")

# Ler a planilha de Excel
planilha = pd.read_excel(arquivo_excel, sheet_name='RESUMO')

# Verificar o estoque de cada produto
produtos_sem_estoque = []

for index, row in planilha.iterrows():
    cod_produto = row['COD_PRODUTO']
    cod_cor = row['COD_COR']
    tamanho = row['TAMANHO']
    quantidade_estoque, nome_cor = consultar_estoque(cursor, cod_produto, cod_cor, tamanho, filiais)

    if quantidade_estoque is None:
        print(f"Erro ao consultar estoque para Produto: {cod_produto}, Cor: {cod_cor}, Tamanho: {tamanho}, Estampa: 0")
        continue

    if quantidade_estoque < row['QUANTIDADE']:
        produtos_sem_estoque.append({
            'produto': cod_produto,
            'cor': cod_cor,
            'nome_cor': nome_cor,
            'tamanho': tamanho,
            'estampa': '0',
            'quantidade_requerida': row['QUANTIDADE'],
            'quantidade_estoque': quantidade_estoque
        })

# Selecionar o local para salvar o arquivo de texto
arquivo_txt = asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")],
                                title="Salvar relatório de produtos sem estoque")

# Salvar o resultado em um arquivo de texto
if arquivo_txt:
    with open(arquivo_txt, 'w') as file:
        if produtos_sem_estoque:
            file.write("Produtos sem estoque:\n")
            for item in produtos_sem_estoque:
                file.write(
                    f"Produto: {item['produto']}, Cor: {item['cor']} ({item['nome_cor']}), Tamanho: {item['tamanho']}, Estampa: {item['estampa']}, Quantidade Requerida: {item['quantidade_requerida']}, Quantidade em Estoque: {item['quantidade_estoque']}\n")
        else:
            file.write("Todos os produtos estão em estoque.")

# Fechar a conexão com o banco de dados
con.close()
