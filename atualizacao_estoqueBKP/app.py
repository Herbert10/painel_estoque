from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads/'


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Salvar o arquivo carregado
        if 'file' not in request.files:
            return 'Nenhum arquivo selecionado'
        file = request.files['file']
        if file.filename == '':
            return 'Nenhum arquivo selecionado'
        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            # Ler o arquivo XLSX especificando o motor
            df = pd.read_excel(filepath, engine='openpyxl')
            session['filename'] = file.filename
            session['partial'] = {}
            # Renderizar o formulário com os dados do DataFrame
            return render_template('formulario.html', df=df, titles=df.columns.values, filename=file.filename,
                                   partial={})
    return render_template('upload.html')


@app.route('/salvar/<filename>', methods=['POST'])
def salvar(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_excel(filepath, engine='openpyxl')

    # Receber os dados do formulário
    dados_formulario = request.form.to_dict(flat=False)

    # Garantir que a quantidade de valores corresponde ao número de linhas do DataFrame
    estoque_atual = dados_formulario.get('estoque_atual', [])
    reposicao = dados_formulario.get('reposicao', [])

    # Preencher valores em branco com um valor padrão, como zero
    estoque_atual = [v if v != '' else '0' for v in estoque_atual]
    reposicao = [v if v != '' else '0' for v in reposicao]

    if len(estoque_atual) != len(df):
        return 'Erro: O número de valores em Estoque Atual não corresponde ao número de linhas do DataFrame'
    if len(reposicao) != len(df):
        return 'Erro: O número de valores em Reposição não corresponde ao número de linhas do DataFrame'

    # Adicionar os novos dados às colunas do DataFrame
    df['ESTOQUE_ATUAL'] = estoque_atual
    df['REPOSICAO'] = reposicao

    # Salvar os dados em um novo arquivo XLSX
    output_filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'dados_atualizados.xlsx')
    df.to_excel(output_filepath, index=False)

    # Limpar os dados parciais da sessão
    session.pop('partial', None)

    return f'Arquivo salvo em: {output_filepath}'


@app.route('/salvar_parcial/<filename>', methods=['POST'])
def salvar_parcial(filename):
    dados_formulario = request.form.to_dict(flat=False)
    partial_data = session.get('partial', {})

    for i in range(len(dados_formulario['estoque_atual'])):
        partial_data[i] = {
            'estoque_atual': str(dados_formulario['estoque_atual'][i]),
            'reposicao': str(dados_formulario['reposicao'][i])
        }

    session['partial'] = partial_data
    return 'Dados salvos parcialmente'


if __name__ == '__main__':
    app.run(debug=True)
