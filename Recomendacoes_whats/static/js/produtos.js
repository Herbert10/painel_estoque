document.addEventListener("DOMContentLoaded", function () {
    carregarProdutos();

    document.getElementById("enviar-mensagem").addEventListener("click", function () {
        enviarMensagem();
    });
});

function formatarData(data) {
    if (!data) return "N/A";
    const date = new Date(data);
    const dia = String(date.getDate()).padStart(2, "0");
    const mes = String(date.getMonth() + 1).padStart(2, "0");
    const ano = date.getFullYear();
    return `${dia}/${mes}/${ano}`;
}

function carregarProdutos() {
    fetch('/buscar-produtos')
        .then(response => response.json())
        .then(produtos => {
            const tabela = document.getElementById("produtos-table").querySelector("tbody");
            const clienteNome = document.getElementById("cliente-nome");
            tabela.innerHTML = "";

            if (produtos.length === 0) {
                clienteNome.textContent = "Cliente: Nenhum produto encontrado.";
                const tr = document.createElement('tr');
                tr.innerHTML = '<td colspan="9" style="text-align: center; color: red;">Nenhum produto encontrado.</td>';
                tabela.appendChild(tr);
                return;
            }

            clienteNome.textContent = `Cliente: ${produtos[0].cliente_nome}`;

            produtos.forEach(produto => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${produto.rank_recomendacao}</td>
                    <td>${produto.produto_nome}</td>
                    <td><img src="${produto.foto_produto}" alt="Imagem do Produto"></td>
                    <td>${produto.qtd_comprada}</td>
                    <td>${produto.total_vendido}</td>
                    <td>${produto.estoque_sp}</td>
                    <td>${formatarData(produto.data_primeira_compra)}</td>
                    <td>${formatarData(produto.data_ultima_compra)}</td>
                    <td><input type="checkbox" class="selecionar-produto" data-produto="${produto.produto_nome}"></td>
                `;
                tabela.appendChild(tr);
            });
        })
        .catch(error => console.error("Erro ao carregar produtos:", error));
}

function enviarMensagem() {
    // Placeholder para a funcionalidade de enviar mensagem
    const observacao = document.getElementById('observacao').value;
    const produtosSelecionados = Array.from(document.querySelectorAll('.selecionar-produto:checked'))
                                    .map(checkbox => checkbox.dataset.produto);

    console.log("Observação:", observacao);
    console.log("Produtos Selecionados:", produtosSelecionados);
    // Aqui você implementaria a lógica para enviar a mensagem e os produtos selecionados para o servidor.
}
