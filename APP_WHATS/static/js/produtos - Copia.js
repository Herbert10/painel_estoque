document.addEventListener("DOMContentLoaded", function () {
    carregarProdutos();

    document.getElementById("enviar-mensagem").addEventListener("click", function () {
        enviarMensagem();
    });
});

function carregarProdutos() {
    const clienteInfo = JSON.parse(sessionStorage.getItem("clienteSelecionado"));

    if (clienteInfo && clienteInfo.nome) {
        document.getElementById("cliente-nome").textContent = `Cliente: ${clienteInfo.nome}`;
    } else {
        document.getElementById("cliente-nome").textContent = "Cliente: Desconhecido";
    }

    fetch('/buscar-produtos')
        .then(response => response.json())
        .then(produtos => {
            const tabela = document.getElementById("produtos-table").querySelector("tbody");
            tabela.innerHTML = "";

            if (produtos.length === 0) {
                tabela.innerHTML = '<tr><td colspan="9" style="text-align: center; color: red;">Nenhum produto encontrado.</td></tr>';
                return;
            }

            produtos.forEach(produto => {
                console.log("Produto carregado:", produto); // Log dos produtos carregados
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${produto.rank_recomendacao || "N/A"}</td>
                    <td>${produto.produto_nome || "N/A"}</td>
                    <td><img src="${produto.foto_produto || "#"}" alt="Imagem do Produto" style="width: 100px; height: auto;"></td>
                    <td>${produto.qtd_comprada || 0}</td>
                    <td>${produto.total_vendido || 0}</td>
                    <td>${produto.estoque_sp || 0}</td>
                    <td>${produto.data_primeira_compra || "N/A"}</td>
                    <td>${produto.data_ultima_compra || "N/A"}</td>
                    <td>
                        <input 
                            type="checkbox" 
                            class="selecionar-produto" 
                            data-produto="${produto.produto_nome || ""}" 
                            data-imagem="${produto.foto_produto || ""}" 
                            data-descricao="${produto.produto_nome || ""}">
                    </td>
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
    const imagens = Array.from(checkboxes).map(cb => cb.dataset.imagem);
    const descricoes = Array.from(checkboxes).map(cb => cb.dataset.descricao);

    console.log("Produtos selecionados:", produtosSelecionados); // Log dos produtos
    console.log("Imagens selecionadas:", imagens); // Log das imagens
    console.log("Descrições selecionadas:", descricoes); // Log das descrições

    if (produtosSelecionados.length === 0) {
        alert("Selecione pelo menos um produto para enviar.");
        return;
    }

    const data = {
        observacao: observacao,
        imagens: imagens,
        descricoes: descricoes
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
            } else if (data.error) {
                alert(`Erro: ${data.error}`);
            }
        })
        .catch(error => console.error("Erro ao enviar mensagem:", error));
}
