function buscarClientes() {
    const codigo = document.getElementById('codigo').value;
    const nome = document.getElementById('nome').value;
    const vendedor = document.getElementById('vendedor').value;

    const query = `?codigo=${codigo}&nome=${nome}&vendedor=${vendedor}`;
    fetch('/buscar-cliente' + query)
        .then(response => response.json())
        .then(clientes => {
            const tabela = document.getElementById('clientes-table').querySelector('tbody');
            tabela.innerHTML = ''; // Limpa a tabela antes de preencher

            if (clientes.length === 0) {
                // Exibe uma mensagem se nenhum cliente for encontrado
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="6" style="text-align: center; color: red;">Nenhum cliente encontrado.</td>';
                tabela.appendChild(tr);
                return;
            }

            // Preenche a tabela com os clientes encontrados
            clientes.forEach(cliente => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${cliente.codigo}</td>
                    <td>${cliente.nome}</td>
                    <td>${cliente.classificacao}</td>
                    <td>${cliente.ultima_compra}</td>
                    <td>${cliente.qtd_produtos}</td>
                    <td><button class="select-button" onclick="irParaProdutos(${cliente.codigo})">Selecionar</button></td>
                `;
                tabela.appendChild(tr);
            });
        })
        .catch(error => {
            console.error('Erro ao buscar clientes:', error);
            alert('Erro ao carregar clientes. Tente novamente.');
        });
}

function irParaProdutos(codigo) {
    window.location.href = `/produtos/${codigo}`;
}
