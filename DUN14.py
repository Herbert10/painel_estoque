import pandas as pd
import tkinter as tk
from tkinter import filedialog

# Função para calcular o dígito verificador usando a regra R1
def calcular_digito_verificador(codigo):
    soma = 0
    for i, digito in enumerate(reversed(codigo)):
        peso = 3 if i % 2 == 0 else 1
        soma += int(digito) * peso
    modulo = soma % 10
    return 10 - modulo if modulo != 0 else 0

# Função para gerar o código EAN-14 com prefixo dinâmico
def gerar_ean14(codigo_ean13, prefixo):
    codigo_base = prefixo + codigo_ean13[:-1]  # Adiciona o prefixo no início e remove o último dígito do EAN-13
    digito_verificador = calcular_digito_verificador(codigo_base)
    return codigo_base + str(digito_verificador)

# Função principal para selecionar o arquivo e processar os dados
def processar_planilha():
    # Criar uma interface Tkinter
    root = tk.Tk()
    root.withdraw()  # Ocultar a janela principal

    # Abrir diálogo para selecionar o arquivo Excel
    caminho_arquivo = filedialog.askopenfilename(title="Selecione a planilha Excel", filetypes=[("Excel files", "*.xlsx")])
    if not caminho_arquivo:
        print("Nenhum arquivo selecionado. Saindo...")
        return

    # Carregar a planilha Excel
    df = pd.read_excel(caminho_arquivo)

    # Aplicar a função para gerar EAN-14 com prefixo '1' e '2'
    df['EAN-14_1'] = df['BARRA'].astype(str).apply(gerar_ean14, prefixo='1')
    df['EAN-14_2'] = df['BARRA'].astype(str).apply(gerar_ean14, prefixo='2')

    # Abrir diálogo para selecionar o local de salvamento do arquivo Excel processado
    caminho_salvar = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Salvar planilha atualizada como")
    if not caminho_salvar:
        print("Nenhum local de salvamento selecionado. Saindo...")
        return

    # Salvar o arquivo Excel com as novas colunas
    df.to_excel(caminho_salvar, index=False)

    print("Processo concluído e planilha salva com sucesso.")

# Executar a função principal
processar_planilha()
