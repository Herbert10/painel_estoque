<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Formulário de Estoque</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="header">
        <h1>Formulário de Estoque</h1>
    </div>
    <div class="client-info">
        <h2>Informações do Cliente</h2>
        <p><strong>Código do Cliente:</strong> {{ df['COD_CLIENTE'][0] }}</p>
        <p><strong>Nome:</strong> {{ df['NOME'][0] }}</p>
        <p><strong>Total de Vendas:</strong> {{ df['QUANTIDADE'].sum() }}</p>
        <button id="verRomaneios">Ver Romaneios</button>
    </div>

    <!-- Formulário de Busca -->
    <form id="searchForm">
        <label for="search_cod_produto">Código do Produto:</label>
        <input type="text" id="search_cod_produto" name="search_cod_produto">

        <label for="search_descricao">Descrição:</label>
        <input type="text" id="search_descricao" name="search_descricao">

        <label for="search_cod_barras">Código de Barras:</label>
        <input type="text" id="search_cod_barras" name="search_cod_barras">

        <label for="search_colecao">Coleção:</label>
        <input type="text" id="search_colecao" name="search_colecao">

        <button type="button" id="searchButton">Buscar</button>
        <button type="button" id="clearButton">Limpar Filtro</button>
    </form>

    <form method="POST" action="{{ url_for('salvar', filename=filename) }}">
        <table>
            <thead>
                <tr>
                    <th>COD_PRODUTO</th>
                    <th>DESCRICAO_PRODUTO</th>
                    <th>COD_COR</th>
                    <th>DESCRICAO_COR</th>
                    <th>TAMANHO</th>
                    <th>PTC</th>
                    <th>QUANTIDADE</th>
                    <th>PRECO</th>
                    <th>FOTO</th>
                    <th>ESTOQUE_ATUAL</th>
                    <th>REPOSICAO</th>
                    <th>DETALHES</th>
                </tr>
            </thead>
            <tbody id="productTableBody">
                {% for row in df.itertuples() %}
                <tr>
                    <td><input type="hidden" name="cod_produto" value="{{ row.COD_PRODUTO }}">{{ row.COD_PRODUTO }}</td>
                    <td><input type="hidden" name="descricao_produto" value="{{ row.DESCRICAO_PRODUTO }}">{{ row.DESCRICAO_PRODUTO }}</td>
                    <td><input type="hidden" name="cod_cor" value="{{ row.COD_COR }}">{{ row.COD_COR }}</td>
                    <td><input type="hidden" name="descricao_cor" value="{{ row.DESCRICAO_COR }}">{{ row.DESCRICAO_COR }}</td>
                    <td><input type="hidden" name="tamanho" value="{{ row.TAMANHO }}">{{ row.TAMANHO }}</td>
                    <td>{{ row.PTC }}</td>
                    <td><input type="hidden" name="quantidade" value="{{ row.QUANTIDADE }}">{{ row.QUANTIDADE }}</td>
                    <td><input type="hidden" name="preco" value="{{ row.PRECO }}">{{ row.PRECO }}</td>
                    <td><input type="hidden" name="foto" value="{{ row.FOTO }}"><img src="{{ row.FOTO }}" alt="Foto do Produto" width="50"></td>
                    <td><input type="text" name="estoque_atual"></td>
                    <td><input type="text" name="reposicao"></td>
                    <td><button type="button" class="btn detalhes-btn" data-produto="{{ row.COD_PRODUTO }}" data-cor="{{ row.COD_COR }}" data-tamanho="{{ row.TAMANHO }}">Detalhes</button></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        <button type="submit">Salvar</button>
    </form>

    <!-- Modal Romaneios -->
    <div id="romaneiosModal" class="modal">
        <div class="modal-content">
            <span class="close" id="closeRomaneios">&times;</span>
            <h2>Romaneios</h2>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>ROMANEIO</th>
                        <th>DATA</th>
                    </tr>
                </thead>
                <tbody id="romaneiosBody">
                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal Detalhes -->
    <div id="detalhesModal" class="modal">
        <div class="modal-content">
            <span class="close" id="closeDetalhes">&times;</span>
            <h2>Detalhes do Produto</h2>
            <table class="table table-bordered">
                <thead>
                    <tr>
                        <th>ROMANEIO</th>
                        <th>DATA</th>
                        <th>QUANTIDADE</th>
                        <th>PRECO</th>
                    </tr>
                </thead>
                <tbody id="detalhesBody">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        document.getElementById('searchButton').onclick = function() {
            const formData = new FormData(document.getElementById('searchForm'));

            fetch('/filtrar_produtos', {
                method: 'POST',
                body: new URLSearchParams(formData)
            })
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('productTableBody');
                tbody.innerHTML = '';

                data.forEach(produto => {
                    const row = `
                        <tr>
                            <td><input type="hidden" name="cod_produto" value="${produto.cod_produto}">${produto.cod_produto}</td>
                            <td><input type="hidden" name="descricao_produto" value="${produto.descricao_produto}">${produto.descricao_produto}</td>
                            <td><input type="hidden" name="cod_cor" value="${produto.cod_cor}">${produto.cod_cor}</td>
                            <td><input type="hidden" name="descricao_cor" value="${produto.descricao_cor}">${produto.descricao_cor}</td>
                            <td><input type="hidden" name="tamanho" value="${produto.tamanho}">${produto.tamanho}</td>
                            <td>${produto.ptc}</td>
                            <td><input type="hidden" name="quantidade" value="${produto.quantidade}">${produto.quantidade}</td>
                            <td><input type="hidden" name="preco" value="${produto.preco}">${produto.preco}</td>
                            <td><input type="hidden" name="foto" value="${produto.foto}"><img src="${produto.foto}" alt="Foto do Produto" width="50"></td>
                            <td><input type="text" name="estoque_atual"></td>
                            <td><input type="text" name="reposicao"></td>
                            <td><button type="button" class="btn detalhes-btn" data-produto="${produto.cod_produto}" data-cor="${produto.cod_cor}" data-tamanho="${produto.tamanho}">Detalhes</button></td>
                        </tr>`;
                    tbody.insertAdjacentHTML('beforeend', row);
                });
            });
        };

        document.getElementById('clearButton').onclick = function() {
            fetch('/limpar_filtros', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: `cod_cliente=${document.querySelector('input[name="cod_cliente"]').value}&data_inicial=${document.querySelector('input[name="data_inicial"]').value}&data_final=${document.querySelector('input[name="data_final"]').value}`
            })
            .then(response => response.json())
            .then(data => {
                const tbody = document.getElementById('productTableBody');
                tbody.innerHTML = '';

                data.forEach(produto => {
                    const row = `
                        <tr>
                            <td><input type="hidden" name="cod_produto" value="${produto.cod_produto}">${produto.cod_produto}</td>
                            <td><input type="hidden" name="descricao_produto" value="${produto.descricao_produto}">${produto.descricao_produto}</td>
                            <td><input type="hidden" name="cod_cor" value="${produto.cod_cor}">${produto.cod_cor}</td>
                            <td><input type="hidden" name="descricao_cor" value="${produto.descricao_cor}">${produto.descricao_cor}</td>
                            <td><input type="hidden" name="tamanho" value="${produto.tamanho}">${produto.tamanho}</td>
                            <td>${produto.ptc}</td>
                            <td><input type="hidden" name="quantidade" value="${produto.quantidade}">${produto.quantidade}</td>
                            <td><input type="hidden" name="preco" value="${produto.preco}">${produto.preco}</td>
                            <td><input type="hidden" name="foto" value="${produto.foto}"><img src="${produto.foto}" alt="Foto do Produto" width="50"></td>
                            <td><input type="text" name="estoque_atual"></td>
                            <td><input type="text" name="reposicao"></td>
                            <td><button type="button" class="btn detalhes-btn" data-produto="${produto.cod_produto}" data-cor="${produto.cod_cor}" data-tamanho="${produto.tamanho}">Detalhes</button></td>
                        </tr>`;
                    tbody.insertAdjacentHTML('beforeend', row);
                });
            });
        };

        document.querySelectorAll('.detalhes-btn').forEach(button => {
            button.onclick = function() {
                const codProduto = this.getAttribute('data-produto');
                const codCor = this.getAttribute('data-cor');
                const tamanho = this.getAttribute('data-tamanho');
                const codCliente = '{{ cod_cliente }}';
                const dataInicial = '{{ data_inicial }}';
                const dataFinal = '{{ data_final }}';

                fetch('/detalhes_produto', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: `cod_cliente=${codCliente}&data_inicial=${dataInicial}&data_final=${dataFinal}&cod_produto=${codProduto}&cod_cor=${codCor}&tamanho=${tamanho}`
                })
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('detalhesBody');
                    tbody.innerHTML = '';

                    data.forEach(detalhe => {
                        const row = `<tr><td>${detalhe.romaneio}</td><td>${detalhe.data}</td><td>${detalhe.quantidade}</td><td>${detalhe.preco}</td></tr>`;
                        tbody.insertAdjacentHTML('beforeend', row);
                    });
                    document.getElementById('detalhesModal').style.display = 'block';
                });
            };
        });

        document.getElementById('closeRomaneios').onclick = function() {
            document.getElementById('romaneiosModal').style.display = 'none';
        };

        document.getElementById('closeDetalhes').onclick = function() {
            document.getElementById('detalhesModal').style.display = 'none';
        };
    </script>
</body>
</html>
