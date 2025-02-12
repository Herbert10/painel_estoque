import React, { useState, useEffect } from "react";

function ConferenciaProduto({ pedido }) {
  const [produtos, setProdutos] = useState([]);
  const [codigoBarras, setCodigoBarras] = useState("");

  useEffect(() => {
    if (pedido) {
      fetch(`http://localhost:8000/produtos/${pedido.numero}`)
        .then((res) => res.json())
        .then((data) => setProdutos(data));
    }
  }, [pedido]);

  const conferirProduto = () => {
    fetch("http://localhost:8000/atualizar_conferencia", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prefaturamento: pedido.numero,
        ptc: codigoBarras,
        quantidade_conferida: 1,
      }),
    }).then(() => {
      alert("Produto conferido!");
      setCodigoBarras("");
    });
  };

  return (
    <div>
      <h1>Conferência do Pedido {pedido?.numero}</h1>
      <input
        type="text"
        value={codigoBarras}
        onChange={(e) => setCodigoBarras(e.target.value)}
        placeholder="Escaneie o código de barras"
      />
      <button onClick={conferirProduto}>Confirmar</button>
      <h2>Produtos do Pedido</h2>
      <ul>
        {produtos.map((produto) => (
          <li key={produto.ptc}>
            {produto.produto} - {produto.cor} - {produto.tamanho} ({produto.quantidade})
          </li>
        ))}
      </ul>
    </div>
  );
}

export default ConferenciaProduto;
