import os
import datetime
import tkinter as tk
from tkinter import filedialog
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.common import I2of5
from reportlab.graphics import renderPDF


def selecionar_arquivo():
    root = tk.Tk()
    root.withdraw()
    arquivo = filedialog.askopenfilename(title="Selecione o arquivo de remessa", filetypes=[("Arquivos REM", "*.rem")])
    return arquivo


def selecionar_diretorio():
    root = tk.Tk()
    root.withdraw()
    diretorio = filedialog.askdirectory(title="Selecione onde salvar os boletos")
    return diretorio


def calcular_fator_vencimento(data_vencimento):
    try:
        data_vencimento = data_vencimento.strip()

        # Verifica se a data é válida e tem 6 dígitos numéricos
        if not data_vencimento.isdigit() or len(data_vencimento) != 6:
            print(f"Data de vencimento inválida: {data_vencimento}. Usando '0000'.")
            return "0000"

        data_base = datetime.date(1997, 10, 7)
        data_venc = datetime.datetime.strptime(data_vencimento, "%d%m%y").date()
        fator = (data_venc - data_base).days

        return str(fator).zfill(4)

    except Exception as e:
        print(f"Erro ao calcular fator de vencimento: {e}. Usando '0000'.")
        return "0000"


def calcular_digito_verificador(codigo):
    pesos = [2, 3, 4, 5, 6, 7, 8, 9]
    soma = 0
    multiplicadores = pesos * ((len(codigo) // len(pesos)) + 1)
    for i, num in enumerate(reversed(codigo)):
        soma += int(num) * multiplicadores[i]
    resto = soma % 11
    dv = 11 - resto
    return '1' if dv in [0, 10, 11] else str(dv)


def gerar_codigo_barras(boleto):
    try:
        campo_livre = f"{boleto['agencia'].zfill(4)}{boleto['carteira'].zfill(2)}{boleto['nosso_numero'].zfill(11)}{boleto['conta'].zfill(7)}0"
        fator_venc = calcular_fator_vencimento(boleto['vencimento'])
        valor_formatado = str(int(boleto['valor'] * 100)).zfill(10)

        codigo_base = f"2379{fator_venc}{valor_formatado}{campo_livre}"
        dv = calcular_digito_verificador(codigo_base)
        codigo_final = codigo_base[:4] + dv + codigo_base[4:]

        return codigo_final

    except Exception as e:
        print(f"Erro ao gerar código de barras: {e}")
        return "00000000000000000000000000000000000000000000"


def gerar_pdf_boleto(boleto, pasta_destino):
    try:
        arquivo_pdf = os.path.join(pasta_destino, f"Boleto_{boleto['nosso_numero']}.pdf")
        c = Canvas(arquivo_pdf, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20 * mm, 270 * mm, "Boleto Bancário - Bradesco")
        c.setFont("Helvetica", 12)
        c.drawString(20 * mm, 260 * mm, f"Nosso Número: {boleto['nosso_numero']}")
        c.drawString(20 * mm, 250 * mm, f"Valor: R$ {boleto['valor']:.2f}")
        c.drawString(20 * mm, 240 * mm, f"Vencimento: {boleto['vencimento']}")
        c.drawString(20 * mm, 230 * mm, f"Pagador: {boleto['pagador']}")
        c.drawString(20 * mm, 220 * mm, f"Endereço: {boleto['endereco']}, {boleto['cep']}-{boleto['sufixo_cep']}")

        # Gerar código de barras
        codigo_barras = gerar_codigo_barras(boleto)
        barcode = I2of5(codigo_barras, xdim=0.8 * mm, checksum=0, bearers=0)
        d = Drawing(103 * mm, 13 * mm)
        d.add(barcode)
        renderPDF.draw(d, c, 20 * mm, 50 * mm)

        c.save()
        return arquivo_pdf

    except Exception as e:
        print(f"Erro ao gerar o PDF do boleto {boleto['nosso_numero']}: {e}")


def ler_arquivo_remessa(caminho_arquivo):
    boletos = []
    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
        for linha in arquivo:
            if linha.startswith("1"):  # Registro de transação
                boleto = {
                    "agencia": linha[2:6].strip(),
                    "conta": linha[13:19].strip(),
                    "carteira": linha[24:26].strip(),
                    "nosso_numero": linha[26:37].strip(),
                    "valor": float(linha[127:139].strip()) / 100 if linha[127:139].strip().isdigit() else 0.0,
                    "vencimento": linha[121:127].strip(),
                    "pagador": linha[235:275].strip(),
                    "endereco": linha[275:315].strip(),
                    "cep": linha[327:331].strip(),
                    "sufixo_cep": linha[332:334].strip()
                }

                # Validação extra para garantir que os dados são válidos
                if len(boleto["vencimento"]) != 6 or not boleto["vencimento"].isdigit():
                    boleto["vencimento"] = "000000"
                    print(f"Aviso: Data de vencimento inválida para {boleto['nosso_numero']}, definida como '000000'.")

                boletos.append(boleto)

    return boletos


def main():
    arquivo_remessa = selecionar_arquivo()
    if not arquivo_remessa:
        print("Nenhum arquivo selecionado.")
        return

    pasta_destino = selecionar_diretorio()
    if not pasta_destino:
        print("Nenhuma pasta selecionada.")
        return

    boletos = ler_arquivo_remessa(arquivo_remessa)
    for boleto in boletos:
        gerar_pdf_boleto(boleto, pasta_destino)
    print(f"Boletos gerados em {pasta_destino}")


if __name__ == "__main__":
    main()
