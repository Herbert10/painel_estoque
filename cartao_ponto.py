from flask import Flask, render_template, request, redirect, url_for
import cv2
import easyocr
import pandas as pd
import re
import os

app = Flask(__name__)

# Criar diretório de saída
output_dir = r"C:\dados"
os.makedirs(output_dir, exist_ok=True)

# Inicializar o leitor do EasyOCR
reader = easyocr.Reader(['pt', 'en'])  # Suporta português e inglês


def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return img


# Função para extrair texto da imagem
def extract_text(image_path):
    text = reader.readtext(image_path, detail=0)  # Extrai o texto sem detalhes
    print("Texto extraído:", text)  # Log para depuração
    return " ".join(text)


# Função para processar o texto extraído
def process_text(text):
    funcionario = re.search(r"([A-Z ]+)", text)
    empresa = re.search(r"Empresa: ([A-Za-z0-9 .,&-]+)", text)
    cnpj = re.search(r"CNPJ: ([0-9./-]+)", text)
    horario = re.search(r"Horário: ([0-9:]+ às [0-9:]+)", text)
    mes_ano = re.search(r"([A-Za-z]+/[0-9]{4})", text)
    turma = re.search(r"Turma ([0-9]+)", text)

    funcionario = funcionario.group(1).strip() if funcionario else "Desconhecido"
    empresa = empresa.group(1) if empresa else "Não encontrado"
    cnpj = cnpj.group(1) if cnpj else "Não encontrado"
    horario = horario.group(1) if horario else "Não informado"
    mes_ano = mes_ano.group(1) if mes_ano else "Não identificado"
    turma = turma.group(1) if turma else "Não especificada"

    # Encontrar todos os registros de horários associados a cada dia
    linhas = text.split(" ")
    registros = []
    for linha in linhas:
        numeros = re.findall(r"\d{2}:\d{2}", linha)
        if numeros:
            registros.append(numeros)

    print("Horários identificados:", registros)  # Log para depuração
    return funcionario, empresa, cnpj, horario, mes_ano, turma, registros


# Função para gerar Excel
def generate_excel(data, funcionario):
    output_path = os.path.join(output_dir, f"{funcionario}_relatorio_ponto.xlsx")
    colunas = ["Funcionário", "Empresa", "CNPJ", "Horário", "Mês/Ano", "Turma", "Data", "Entrada Manhã", "Saída Manhã",
               "Entrada Tarde", "Saída Tarde", "Entrada Extra", "Saída Extra"]
    df = pd.DataFrame(data, columns=colunas)
    df.to_excel(output_path, index=False)
    print(f"Relatório gerado: {output_path}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        image_path = os.path.join(output_dir, file.filename)
        file.save(image_path)
        text = extract_text(image_path)
        funcionario, empresa, cnpj, horario, mes_ano, turma, registros = process_text(text)

        data = []
        for i, registro in enumerate(registros, start=1):
            entrada_manha = registro[0] if len(registro) > 0 else ""
            saida_manha = registro[1] if len(registro) > 1 else ""
            entrada_tarde = registro[2] if len(registro) > 2 else ""
            saida_tarde = registro[3] if len(registro) > 3 else ""
            entrada_extra = registro[4] if len(registro) > 4 else ""
            saida_extra = registro[5] if len(registro) > 5 else ""

            data.append(
                [funcionario, empresa, cnpj, horario, mes_ano, turma, i, entrada_manha, saida_manha, entrada_tarde,
                 saida_tarde, entrada_extra, saida_extra])

        generate_excel(data, funcionario)
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
