import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename

def process_excel_file():
    # Desativar janela principal do Tkinter
    Tk().withdraw()

    # Selecionar o arquivo de entrada
    input_file = askopenfilename(title="Selecione o arquivo Excel de entrada", filetypes=[("Excel files", "*.xlsx")])
    if not input_file:
        print("Nenhum arquivo selecionado.")
        return

    # Ler o arquivo Excel, garantindo que os campos específicos sejam tratados como texto
    df = pd.read_excel(input_file, dtype={'COD_PRODUTO': str, 'COD_COR': str, 'COD_ESTAMPA': str})

    # Agrupar por COD_PRODUTO e somar as colunas QUANTIDADE e TOTAL
    aggregated = df.groupby(['COD_PRODUTO']).agg({
        'QUANTIDADE': 'sum',
        'TOTAL': 'sum'
    }).reset_index()

    # Obter a primeira ocorrência de cada COD_PRODUTO
    first_rows = df.drop_duplicates(subset='COD_PRODUTO', keep='first').set_index('COD_PRODUTO')

    # Atualizar as colunas QUANTIDADE, TOTAL e recalcular o PREÇO unitário
    first_rows['QUANTIDADE'] = aggregated.set_index('COD_PRODUTO')['QUANTIDADE']
    first_rows['TOTAL'] = aggregated.set_index('COD_PRODUTO')['TOTAL']
    first_rows['PRECO'] = first_rows['TOTAL'] / first_rows['QUANTIDADE']

    # Selecionar o local de salvamento
    output_file = asksaveasfilename(title="Selecione onde salvar o arquivo Excel processado", defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    if not output_file:
        print("Nenhum local de salvamento selecionado.")
        return

    # Salvar o arquivo processado
    first_rows.reset_index().to_excel(output_file, index=False)
    print(f"Arquivo processado salvo em: {output_file}")

# Executar a rotina
process_excel_file()
