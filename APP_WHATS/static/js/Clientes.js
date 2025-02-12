document.addEventListener("DOMContentLoaded", function () {
    carregarVendedores();
    configurarOrdenacao();
    document.getElementById("buscar-clientes").addEventListener("click", buscarClientes);

    // Verifica se há clientes salvos e restaura sem recarregar do servidor
    restaurarResultados();
});

// Função para carregar os vendedores no select e restaurar filtros depois
function carregarVendedores() {
    fetch('/buscar-vendedores')
        .then(response => response.json())
        .then(vendedores => {
            const selectVendedor = document.getElementById("vendedor");
            selectVendedor.innerHTML = '<option value="">Todos</option>'; // Reseta o select

            vendedores.forEach(vendedor => {
                const option = document.createElement("option");
                option.value = vendedor;
                option.textContent = vendedor;
                selectVendedor.appendChild(option);
            });

            // Restaurar filtros após carregar os vendedores
            restaurarFiltros();
        })
        .catch(error => console.error("Erro ao carregar vendedores:", error));
}

// Função para buscar clientes e salvar os filtros e resultados
function buscarClientes() {
    console.log("Buscando clientes...");

    const codigo = document.getElementById("codigo").value.trim();
    const nome = document.getElementById("nome").value.trim();
    const vendedor = document.getElementById("vendedor").value.trim();

    // Salvar filtros no sessionStorage
    sessionStorage.setItem("filtrosClientes", JSON.stringify({ codigo, nome, vendedor }));

    const queryParams = new URLSearchParams({
        codigo: codigo || "",
        nome: nome || "",
        vendedor: vendedor || ""
    });

    const spinner = document.querySelector(".spinner");
    spinner.style.display = "block"; // Exibe o carregamento

    fetch(`/buscar-cliente?${queryParams.toString()}`)
        .then(response => response.json())
        .then(clientes => {
            spinner.style.display = "none"; // Oculta o carregamento

            if (clientes.length === 0) {
                sessionStorage.removeItem("resultadosClientes"); // Remove se não houver resultados
            } else {
                sessionStorage.setItem("resultadosClientes", JSON.stringify(clientes)); // Salva os resultados
            }

            exibirClientes(clientes);
        })
        .catch(error => {
            console.error("Erro ao buscar clientes:", error);
            spinner.style.display = "none";
        });
}

// Função para restaurar os filtros ao voltar para a página
function restaurarFiltros() {
    const filtrosSalvos = JSON.parse(sessionStorage.getItem("filtrosClientes"));

    if (filtrosSalvos) {
        document.getElementById("codigo").value = filtrosSalvos.codigo || "";
        document.getElementById("nome").value = filtrosSalvos.nome || "";

        const selectVendedor = document.getElementById("vendedor");
        if (selectVendedor) {
            setTimeout(() => {
                selectVendedor.value = filtrosSalvos.vendedor || "";
            }, 100);
        }
    }
}

// Função para restaurar a lista de clientes sem recarregar do servidor
function restaurarResultados() {
    const clientesSalvos = JSON.parse(sessionStorage.getItem("resultadosClientes"));
    if (clientesSalvos) {
        exibirClientes(clientesSalvos);
    }
}

// Função para exibir clientes na tabela
function exibirClientes(clientes) {
    const tabela = document.querySelector("#clientes-table tbody");
    tabela.innerHTML = "";

    if (clientes.length === 0) {
        tabela.innerHTML = '<tr><td colspan="6" style="text-align: center; color: red;">Nenhum cliente encontrado.</td></tr>';
        return;
    }

    clientes.forEach(cliente => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${cliente.codigo}</td>
            <td>${cliente.nome}</td>
            <td>${cliente.classificacao}</td>
            <td>${cliente.ultima_compra}</td>
            <td>${cliente.qtd_produtos}</td>
            <td>
                <button class="selecionar-cliente" 
                    data-id="${cliente.id}" 
                    data-nome="${cliente.nome}">
                    Selecionar
                </button>
            </td>
        `;

        tabela.appendChild(tr);
    });

    // Adiciona evento para destacar o cliente selecionado
    document.querySelectorAll(".selecionar-cliente").forEach(botao => {
        botao.addEventListener("click", function () {
            const clienteId = this.dataset.id;
            const clienteNome = this.dataset.nome;

            // Armazena o cliente selecionado no sessionStorage
            sessionStorage.setItem("clienteSelecionado", JSON.stringify({
                id: clienteId,
                nome: clienteNome
            }));

            // Remove a classe 'selecionado' de todas as linhas
            document.querySelectorAll("#clientes-table tbody tr").forEach(linha => {
                linha.classList.remove("selecionado");
            });

            // Adiciona a classe 'selecionado' à linha correspondente
            this.closest("tr").classList.add("selecionado");

            // Redireciona para a página de produtos
            window.location.href = `/produtos/${clienteId}`;
        });
    });

    // Restaurar o cliente selecionado ao carregar a página
    destacarClienteSelecionado();
}

// Função para destacar o cliente selecionado ao recarregar a página
function destacarClienteSelecionado() {
    const clienteSelecionado = JSON.parse(sessionStorage.getItem("clienteSelecionado"));
    if (clienteSelecionado) {
        document.querySelectorAll("#clientes-table tbody tr").forEach(linha => {
            const nome = linha.cells[1].innerText;
            if (nome === clienteSelecionado.nome) {
                linha.classList.add("selecionado");
            }
        });
    }
}

// Configuração da ordenação das colunas
function configurarOrdenacao() {
    const headers = document.querySelectorAll("#clientes-table th");
    headers.forEach(header => {
        header.addEventListener("click", function () {
            const coluna = this.getAttribute("data-column");
            if (coluna) {
                ordenarTabela(coluna);
            }
        });
    });
}

let direcaoOrdenacao = {};

function ordenarTabela(coluna) {
    const tabela = document.querySelector("#clientes-table tbody");
    const linhas = Array.from(tabela.rows);

    direcaoOrdenacao[coluna] = !direcaoOrdenacao[coluna];
    const ascendente = direcaoOrdenacao[coluna];

    linhas.sort((a, b) => {
        const valorA = a.cells[coluna === "ultima_compra" ? 3 : coluna === "qtd_produtos" ? 4 : coluna === "codigo" ? 0 : coluna === "nome" ? 1 : coluna === "classificacao" ? 2 : 5].innerText;
        const valorB = b.cells[coluna === "ultima_compra" ? 3 : coluna === "qtd_produtos" ? 4 : coluna === "codigo" ? 0 : coluna === "nome" ? 1 : coluna === "classificacao" ? 2 : 5].innerText;

        if (!isNaN(valorA) && !isNaN(valorB)) {
            return ascendente ? valorA - valorB : valorB - valorA;
        } else {
            return ascendente ? valorA.localeCompare(valorB) : valorB.localeCompare(valorA);
        }
    });

    tabela.innerHTML = "";
    linhas.forEach(linha => tabela.appendChild(linha));
}
