document.addEventListener("DOMContentLoaded", function () {
    carregarVendedores();
    configurarEventos();
});

let clientes = [];
let ordemAtual = {};

// Função para carregar os vendedores no dropdown
function carregarVendedores() {
    fetch('/buscar-vendedores')
        .then(response => response.json())
        .then(vendedores => {
            const selectVendedor = document.getElementById("vendedor");
            vendedores.forEach(vendedor => {
                const option = document.createElement("option");
                option.value = vendedor;
                option.textContent = vendedor;
                selectVendedor.appendChild(option);
            });
        })
        .catch(error => console.error("Erro ao carregar vendedores:", error));
}

// Configura os eventos de clique e busca
function configurarEventos() {
    const botaoBuscar = document.getElementById("buscar-clientes");
    const colunasOrdenaveis = document.querySelectorAll("#clientes-table th[data-column]");

    // Evento para buscar clientes
    botaoBuscar.addEventListener("click", buscarClientes);

    // Evento para ordenar colunas
    colunasOrdenaveis.forEach(th => {
        th.addEventListener("click", function () {
            const coluna = this.dataset.column;
            const ordem = ordemAtual[coluna] === "asc" ? "desc" : "asc";
            ordenarClientes(coluna, ordem);
        });
    });
}

// Função para buscar clientes
function buscarClientes() {
    const codigo = document.getElementById("codigo").value.trim();
    const nome = document.getElementById("nome").value.trim();
    const vendedor = document.getElementById("vendedor").value.trim();

    exibirSpinner(true);

    fetch(`/buscar-cliente?codigo=${codigo}&nome=${nome}&vendedor=${vendedor}`)
        .then(response => response.json())
        .then(dados => {
            console.log("Clientes recebidos:", dados);
            clientes = dados;
            atualizarTabela(clientes);
        })
        .catch(error => console.error("Erro ao buscar clientes:", error))
        .finally(() => exibirSpinner(false));
}

// Atualiza a tabela de clientes
function atualizarTabela(clientes) {
    const tabela = document.getElementById("clientes-table").querySelector("tbody");
    tabela.innerHTML = ""; // Limpa a tabela antes de preenchê-la

    if (clientes.length === 0) {
        tabela.innerHTML = '<tr><td colspan="6" style="text-align: center; color: red;">Nenhum cliente encontrado.</td></tr>';
        return;
    }

    clientes.forEach(cliente => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${cliente.cod_cliente || "N/A"}</td>
            <td>${cliente.nome_cliente || "N/A"}</td>
            <td>${cliente.classificacao_cliente || "N/A"}</td>
            <td>${cliente.ultima_compra || "N/A"}</td>
            <td>${cliente.qtd_produtos || 0}</td>
            <td><button onclick="exibirClienteSelecionado(${cliente.cod_cliente})">Selecionar</button></td>
        `;
        tabela.appendChild(tr);
    });
}

// Função para ordenar clientes
function ordenarClientes(coluna, ordem) {
    ordemAtual[coluna] = ordem;
    const comparador = (a, b) => {
        const valorA = a[coluna] || "";
        const valorB = b[coluna] || "";
        return ordem === "asc" ? valorA.localeCompare(valorB) : valorB.localeCompare(valorA);
    };
    const clientesOrdenados = [...clientes].sort(comparador);
    atualizarTabela(clientesOrdenados);
}

// Redireciona para a tela de produtos do cliente selecionado
function exibirClienteSelecionado(clienteId) {
    console.log(`Cliente Selecionado: ${clienteId}`);
    window.location.href = `/produtos/${clienteId}`;
}

// Exibe ou oculta o spinner de carregamento
function exibirSpinner(ativo) {
    const spinner = document.querySelector(".spinner");
    spinner.style.display = ativo ? "flex" : "none";
}
