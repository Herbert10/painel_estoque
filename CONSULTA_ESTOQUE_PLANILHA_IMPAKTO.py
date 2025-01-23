import pandas as pd
import fdb
from tkinter import Tk, ttk, messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.simpledialog import askstring, askinteger
import threading
import sys

# Função para consultar o estoque de um produto no Firebird e obter o nome da cor e a descrição da coleção
def consultar_estoque(cursor, cod_produto, cod_cor, tamanho, filiais):
    try:
        query_estoque = f"""
        SELECT SUM(saldo) AS QUANTIDADE_EM_ESTOQUE,
               (SELECT descricao FROM CORES WHERE cod_cor = '{cod_cor}') AS NOME_COR,
               (SELECT descricao FROM COLECOES WHERE colecao = (SELECT colecao FROM PRODUTOS WHERE cod_produto = '{cod_produto}')) AS COLECAO_DESCRICAO
        FROM ESTOQUES_LOCAIS
        WHERE PRODUTO = (SELECT produto FROM PRODUTOS WHERE cod_produto = '{cod_produto}')
        AND COR = (SELECT cor FROM CORES WHERE cod_cor = '{cod_cor}')
        AND TAMANHO = '{tamanho}'
        AND Estampa = '0'
        AND filial IN ({', '.join(filiais)})
        """
        cursor.execute(query_estoque)
        result = cursor.fetchone()
        quantidade_estoque = result[0] if result[0] is not None else 0
        nome_cor = result[1] if result[1] is not None else 'Desconhecida'
        colecao_descricao = result[2] if result[2] is not None else 'Desconhecida'
        return quantidade_estoque, nome_cor, colecao_descricao
    except fdb.DatabaseError as e:
        print(f"Erro ao executar consulta SQL: {e}")
        return None, None, None

# Função para processar a planilha e consultar os estoques
def processar_planilha(cursor, planilha, filiais, progresso, total_registros, label_progresso):
    produtos_sem_estoque = []
    produtos_com_estoque = []
    produtos_estoque_parcial = []
    produtos_parciais_faltantes = []
    produtos_sem_estoque_txt = []
    produtos_multifilial = []

    for i in range(0, len(planilha), 20):
        chunk = planilha.iloc[i:i+20]
        for j, row in chunk.iterrows():
            cod_produto = row['COD_PRODUTO']
            cod_cor = row['COD_COR']
            tamanho = row['TAMANHO']
            cod_estampa = row['COD_ESTAMPA']
            quantidade_pedida = row['QUANTIDADE']
            preco = row['PRECO']

            quantidade_estoque, nome_cor, colecao_descricao = consultar_estoque(cursor, cod_produto, cod_cor, tamanho, filiais)

            if quantidade_estoque is None:
                print(f"Erro ao consultar estoque para Produto: {cod_produto}, Cor: {cod_cor}, Tamanho: {tamanho}, Estampa: {cod_estampa}")
                continue

            produto_info = {
                'COD_PRODUTO': cod_produto,
                'COD_COR': cod_cor,
                'TAMANHO': tamanho,
                'COD_ESTAMPA': cod_estampa,
                'QUANTIDADE': quantidade_pedida,
                'PRECO': preco,
                'COLECAO': colecao_descricao  # Adiciona a descrição da coleção
            }

            if quantidade_estoque == 0:
                produtos_sem_estoque.append(produto_info)
                produtos_sem_estoque_txt.append({
                    **produto_info,
                    'QUANTIDADE_ESTOQUE': quantidade_estoque
                })
            elif quantidade_estoque < quantidade_pedida:
                produtos_estoque_parcial.append({
                    **produto_info,
                    'QUANTIDADE': quantidade_estoque  # Ajusta a quantidade para o estoque disponível
                })
                produtos_parciais_faltantes.append({
                    **produto_info,
                    'QUANTIDADE_FALTANTE': quantidade_pedida - quantidade_estoque
                })
                produtos_sem_estoque_txt.append({
                    **produto_info,
                    'QUANTIDADE_ESTOQUE': quantidade_estoque
                })
            else:
                produtos_com_estoque.append(produto_info)

            if len(filiais) > 1:
                quantidade_estoque_filial = []
                for filial in filiais:
                    quantidade_estoque_f, _, _ = consultar_estoque(cursor, cod_produto, cod_cor, tamanho, [filial])
                    quantidade_estoque_filial.append(quantidade_estoque_f)
                produtos_multifilial.append({
                    **produto_info,
                    **{f"QUANTIDADE_ESTOQUE_FILIAL_{filial}": quantidade for filial, quantidade in zip(filiais, quantidade_estoque_filial)}
                })

            progresso["value"] = i + len(chunk)
            label_progresso.config(text=f"Processado: {i + len(chunk)} de {total_registros}")
            root.update_idletasks()

    return produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial

# Função para iniciar o processamento
def iniciar_processamento():
    try:
        produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial = processar_planilha(cursor, planilha, filiais_lista, progresso, total_registros, label_progresso)
        root.after(100, lambda: abrir_opcoes(produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial))
    except Exception as e:
        print(f"Erro durante o processamento: {e}")

def abrir_opcoes(produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial):
    root.destroy()
    opcao = askinteger("Opção",
                       "Digite a opção desejada:\n1 - Gerar Excel com produtos com estoque suficiente\n2 - Gerar Excel com produtos com estoque parcial\n3 - Gerar Excel com produtos sem estoque\n4 - Gerar Excel com quantidade faltante dos produtos parciais\n5 - Gerar Excel com produtos sem estoque ou com estoque insuficiente\n6 - Gerar Excel com estoque por filial")
    salvar_opcao(produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial, opcao)

def salvar_opcao(produtos_sem_estoque, produtos_com_estoque, produtos_estoque_parcial, produtos_parciais_faltantes, produtos_sem_estoque_txt, produtos_multifilial, opcao):
    def salvar_arquivo(dataframe, default_extension, filetypes, title, sheet_name):
        arquivo = asksaveasfilename(defaultextension=default_extension, filetypes=filetypes, title=title)
        if arquivo and not dataframe.empty:
            colecao_opcao = askstring("Coleção", "Deseja incluir a coluna de coleção? (S/N)").strip().upper()
            if colecao_opcao == 'N' and 'COLECAO' in dataframe.columns:
                dataframe = dataframe.drop(columns=['COLECAO'])
            dataframe.to_excel(arquivo, index=False, sheet_name=sheet_name)

    if opcao == 1:
        df_produtos_com_estoque = pd.DataFrame(produtos_com_estoque)
        salvar_arquivo(df_produtos_com_estoque, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos com estoque suficiente", "Produtos com Estoque")

    elif opcao == 2:
        df_produtos_estoque_parcial = pd.DataFrame(produtos_estoque_parcial)
        salvar_arquivo(df_produtos_estoque_parcial, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos com estoque parcial", "Produtos com Estoque Parcial")

    elif opcao == 3:
        df_produtos_sem_estoque = pd.DataFrame(produtos_sem_estoque)
        salvar_arquivo(df_produtos_sem_estoque, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos sem estoque", "Produtos sem Estoque")

    elif opcao == 4:
        df_produtos_parciais_faltantes = pd.DataFrame(produtos_parciais_faltantes)
        salvar_arquivo(df_produtos_parciais_faltantes, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos parciais com quantidade faltante", "Produtos Parciais Faltantes")

    elif opcao == 5:
        df_produtos_sem_estoque_txt = pd.DataFrame(produtos_sem_estoque_txt)
        salvar_arquivo(df_produtos_sem_estoque_txt, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos sem estoque ou insuficiente", "Produtos Sem Estoque ou Insuficiente")

    elif opcao == 6:
        df_produtos_multifilial = pd.DataFrame(produtos_multifilial)
        salvar_arquivo(df_produtos_multifilial, ".xlsx", [("Excel files", "*.xlsx")], "Salvar relatório de produtos com estoque por filial", "Produtos Estoque por Filial")

    sys.exit()  # Finalizar o processo

# Configurar conexão com o banco de dados Firebird
with fdb.connect(
    dsn='milleniumflexmetal.ddns.net:c:/sys/base/millennium',
    user='SYSDBA',
    password='masterkey',
    charset='UTF8'
) as con:
    cursor = con.cursor()

    # Selecionar o arquivo Excel
    Tk().withdraw()
    arquivo_excel = askopenfilename(title="Selecione a planilha de resumo", filetypes=[("Excel files", "*.xls *.xlsx *.XLSX")])

    # Perguntar ao usuário quais filiais ele quer consultar
    filiais = askstring("Selecionar Filiais",
                        "Digite os números das filiais separados por vírgulas (2 - Flexmetal, 14 - Orlando, 19 - Megatoon RS):")

    # Verificar se o usuário cancelou a seleção de filiais
    if not filiais:
        print("Seleção de filiais cancelada.")
        exit()

    filiais_lista = [filial.strip() for filial in filiais.split(',')]

    # Ler a planilha de Excel
    planilha = pd.read_excel(arquivo_excel, sheet_name='Planilha1',
                             dtype={'COD_PRODUTO': str, 'COD_COR': str, 'TAMANHO': str, 'COD_ESTAMPA': str, 'QUANTIDADE': int, 'PRECO': float})

    # Configurar a janela de progresso
    root = Tk()
    root.title("Processamento de Planilha")
    progresso = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    progresso.pack(pady=10)
    total_registros = len(planilha)
    progresso["maximum"] = total_registros
    label_progresso = ttk.Label(root, text=f"Processado: 0 de {total_registros}")
    label_progresso.pack(pady=10)
    cancelar = False

    def cancelar_processamento():
        global cancelar
        cancelar = True
        root.destroy()

    button_cancelar = ttk.Button(root, text="Cancelar", command=cancelar_processamento)
    button_cancelar.pack(pady=10)

    # Adicionar rodapé com o texto "Desenvolvido por: Alfa Dash Consultoria e Treinamento Ltda"
    label_rodape = ttk.Label(root, text="Desenvolvido por: Alfa Dash Consultoria e Treinamento Ltda", font=("Helvetica", 10))
    label_rodape.pack(side="bottom", pady=10)

    # Iniciar o processamento em uma thread separada
    thread = threading.Thread(target=iniciar_processamento)
    thread.start()
    root.mainloop()

# Fechar a conexão com o banco de dados
cursor.close()
con.close()
