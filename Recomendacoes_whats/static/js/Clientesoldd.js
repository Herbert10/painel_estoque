document.addEventListener("DOMContentLoaded", function () {
    carregarVendedores();

    // Evento do botão "Buscar"
    document.getElementById("buscar-cliente").addEventListener("click", function () {
        const codigo = document.getElementById("codigo").value;
        const nome = document.getElementById("nome").value;
        const vendedor = document.getElementById("vendedor-selecao").value;
        carregarClientes(codigo, nome, vendedor);
    });

    // Evento para destacar a linha e exibir o cliente selecionado
    document.getElementById("clientes-table").addEventListener("click", function (event) {
        if (event.target.classList.contains("selecionar-cliente")) {
            const linha = event.target.closest("tr");
            const clienteId = linha.getAttribute("data-id");
            marcarLinha(linha);
            exibirClienteSelecionado(clienteId);
        }
    });
});

function carregarVendedores() {
    fetch("/buscar-vendedores")
        .then(response => response.json())
        .then(vendedores => {
            const seletor = document.getElementById("vendedor-selecao");
            vendedores.forEach(vendedor => {
                const option = document.createElement("option");
                option.value = vendedor;
                option.textContent = vendedor;
                seletor.appendChild(option);
            });
        })
        .catch(error => console.error("Erro ao carregar vendedores:", error));
}

function carregarClientes(codigo = "", nome = "", vendedor = "") {
    const url = `/buscar-cliente?codigo=${codigo}&nome=${nome}&vendedor=${vendedor}`;

    const spinner = document.getElementById("loading-spinner");
    spinner.style.display = "block"; // Exibe o spinner durante o carregamento

    fetch(url)
        .then(response => response.json())
        .then(clientes => {
            const tabela = document.getElementById("clientes-table").querySelector("tbody");
            tabela.innerHTML = ""; // Limpa a tabela antes de preencher

            clientes.forEach(cliente => {
                const tr = document.createElement("tr");
                tr.setAttribute("data-id", cliente.id); // Salva o ID do cliente na linha
                tr.innerHTML = `
                    <td>${cliente.codigo}</td>
                    <td>${cliente.nome}</td>
                    <td>${cliente.classificacao}</td>
                    <td>${cliente.ultima_compra}</td>
                    <td>${cliente.qtd_produtos}</td>
                    <td><button class="selecionar-cliente">Selecionar</button></td>
                `;
                tabela.appendChild(tr);
            });

            spinner.style.display = "none"; // Esconde o spinner após carregar os dados
        })
        .catch(error => {
            console.error("Erro ao carregar clientes:", error);
            spinner.style.display = "none"; // Esconde o spinner mesmo em caso de erro
        });
}

function marcarLinha(linha) {
    const linhas = document.querySelectorAll("#clientes-table tbody tr");
    linhas.forEach(l => l.classList.remove("selecionado")); // Remove a marcação das outras linhas
    linha.classList.add("selecionado"); // Marca a linha selecionada
}

function exibirClienteSelecionado(clienteId) {
    const display = document.getElementById("cliente-selecionado");
    display.textContent = `Cliente Selecionado: ${clienteId}`;
    window.location.href = `/produtos/${clienteId}`; // Redireciona para a tela de produtos
}
