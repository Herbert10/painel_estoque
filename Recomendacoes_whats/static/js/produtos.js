document.addEventListener("DOMContentLoaded", function () {
    carregarProdutos();

    document.getElementById("enviar-mensagem").addEventListener("click", function () {
        enviarMensagem();
    });
});

function carregarProdutos() {
    fetch('/buscar-produtos')
        .then(response => response.json())
        .then(produtos => {
            const tabela = document.getElementById("produtos-table").querySelector("tbody");
            const clienteNome = document.getElementById("cliente-nome");
            tabela.innerHTML = ""; // Limpa a tabela antes de preencher

            if (produtos.length === 0) {
                clienteNome.textContent = "Nenhum cliente selecionado ou produtos não encontrados.";
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="9" style="text-align: center; color: red;">Nenhum produto encontrado.</td>';
                tabela.appendChild(tr);
                return;
            }

            clienteNome.textContent = `Cliente: ${produtos[0].cliente_nome || 'Desconhecido'}`;

            produtos.forEach(produto => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${produto.rank_recomendacao}</td>
                    <td>${produto.produto_nome}</td>
                    <td><img src="${produto.foto_produto}" alt="Imagem do Produto"></td>
                    <td>${produto.qtd_comprada}</td>
                    <td>${produto.total_vendido}</td>
                    <td>${produto.estoque_sp}</td>
                    <td>${produto.data_primeira_compra}</td>
                    <td>${produto.data_ultima_compra}</td>
                    <td><input type="checkbox" class="selecionar-produto" data-produto="${produto.produto_nome}"></td>
                `;
                tabela.appendChild(tr);
            });
        })
        .catch(error => console.error("Erro ao carregar produtos:", error));
}

function enviarMensagem() {
    const observacao = document.getElementById("observacao").value;
    const checkboxes = document.querySelectorAll(".selecionar-produto:checked");
    const produtosSelecionados = Array.from(checkboxes).map(cb => cb.dataset.produto);

    if (produtosSelecionados.length === 0) {
        alert("Selecione pelo menos um produto para enviar.");
        return;
    }

    const data = {
        observacao: observacao,
        produtos: produtosSelecionados
    };

    fetch('/enviar-mensagem', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
            }
        })
        .catch(error => console.error("Erro ao enviar mensagem:", error));
}
