document.addEventListener("DOMContentLoaded", function () {
    carregarVendedores();
    configurarEventos();
    buscarClientes(); // Carrega os clientes inicialmente

    // Adicione um console.log para verificar se o evento DOMContentLoaded está sendo disparado
    console.log("DOMContentLoaded disparado!"); 
});

let clientes = [];
let ordemAtual = {};

function carregarVendedores() {
    fetch('/buscar-vendedores')
        .then(response => response.json())
        .then(vendedores => {
            console.log("Vendedores recebidos:", vendedores); // Verifica os vendedores recebidos
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

function configurarEventos() {
    document.getElementById("buscar-clientes").addEventListener("click", buscarClientes);

    document.querySelectorAll("#clientes-table th[data-column]").forEach(th => {
        th.addEventListener("click", function () {
            const coluna = this.dataset.column;
            const ordem = ordemAtual[coluna] === "asc" ? "desc" : "asc";
            ordenarClientes(coluna, ordem);
        });
    });
}

function buscarClientes() {
    const codigo = document.getElementById("codigo").value.trim();
    const nome = document.getElementById("nome").value.trim();
    const vendedor = document.getElementById("vendedor").value; // Corrigido: removido .trim()
    const vendedorCodificado = encodeURIComponent(vendedor);


    exibirSpinner(true);

    console.log("Valores antes do fetch:", { codigo, nome, vendedor }); // Log dos valores antes do fetch

    fetch(`/buscar-cliente?codigo=${codigo}&nome=${nome}&vendedor=${vendedorCodificado}`)
        .then(response => {
            console.log("Resposta do servidor:", response); // Log da resposta do servidor
            return response.json();
        })
        .then(dados => {
            console.log("Dados recebidos:", dados);
            clientes = dados;
            atualizarTabela(clientes);
        })
        .catch(error => console.error("Erro ao buscar clientes:", error))
        .finally(() => exibirSpinner(false));
}

function formatarData(data) {
    if (!data) return "N/A";
    const date = new Date(data);
    const dia = String(date.getDate()).padStart(2, "0");
    const mes = String(date.getMonth() + 1).padStart(2, "0");
    const ano = date.getFullYear();
    return `${dia}/${mes}/${ano}`;
}


function atualizarTabela(clientes) {
    const tabela = document.getElementById("clientes-table").querySelector("tbody");
    tabela.innerHTML = "";

    if (clientes.length === 0) {
        tabela.innerHTML = '<tr><td colspan="6" style="text-align: center; color: red;">Nenhum cliente encontrado.</td></tr>';
        return;
    }

    clientes.forEach(cliente => {
        console.log("Cliente:", cliente);
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${cliente.codigo || "N/A"}</td>
            <td>${cliente.nome || "N/A"}</td>
            <td>${cliente.classificacao || "N/A"}</td>
            <td>${formatarData(cliente.ultima_compra)}</td>
            <td>${cliente.qtd_produtos || 0}</td>
            <td><button onclick="exibirClienteSelecionado(${cliente.id})">Selecionar</button></td>
        `;
        tabela.appendChild(tr);
    });

    console.log("HTML da tabela:", document.getElementById("clientes-table").innerHTML);
}


function ordenarClientes(coluna, ordem) {
    ordemAtual[coluna] = ordem;
    const comparador = (a, b) => {
        const valorA = a[coluna] || "";
        const valorB = b[coluna] || "";
        if (ordem === "asc") return valorA > valorB ? 1 : -1;
        return valorA < valorB ? 1 : -1;
    };
    const clientesOrdenados = [...clientes].sort(comparador);
    atualizarTabela(clientesOrdenados);
}

function exibirClienteSelecionado(clienteId) {
    window.location.href = `/produtos/${clienteId}`;
}

function exibirSpinner(ativo) {
    const spinner = document.querySelector(".spinner");
    spinner.style.display = ativo ? "flex" : "none";
}
