import pandas as pd
from tkinter import Tk, filedialog

def process_txt_to_excel(input_file, output_file):
    data = []
    with open(input_file, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('I|'):
                parts = line.split('|')
                try:
                    codigo_barras = parts[4].split(' - ')[0].strip()
                    quantidade = float(parts[9])
                    valor_unitario = float(parts[10])
                    total = float(parts[11])
                    data.append({
                        'CODIGO DE BARRAS': codigo_barras,
                        'QUANTIDADE': quantidade,
                        'VALOR UNITARIO': valor_unitario,
                        'TOTAL': total
                    })
                except (IndexError, ValueError):
                    continue

    # Criar DataFrame e salvar em Excel
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)
    print(f"Arquivo Excel salvo em: {output_file}")

# Configurar interface para seleção de arquivos
def main():
    root = Tk()
    root.withdraw()  # Ocultar a janela principal do Tkinter

    # Selecionar o arquivo .txt
    input_file = filedialog.askopenfilename(
        title="Selecione o arquivo .txt",
        filetypes=[("Arquivos de Texto", "*.txt")]
    )
    if not input_file:
        print("Nenhum arquivo selecionado.")
        return

    # Selecionar o local de salvamento do Excel
    output_file = filedialog.asksaveasfilename(
        title="Salvar arquivo Excel",
        defaultextension=".xlsx",
        filetypes=[("Arquivo Excel", "*.xlsx")]
    )
    if not output_file:
        print("Local de salvamento não especificado.")
        return

    # Processar o arquivo
    process_txt_to_excel(input_file, output_file)

if __name__ == "__main__":
    main()
