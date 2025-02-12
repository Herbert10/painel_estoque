import React, { useState, useEffect } from "react";
import "./styles.css";

function Conferencia({ pedido, voltar }) {
  const [produtos, setProdutos] = useState([]);
  const [codigoBarras, setCodigoBarras] = useState("");
  const [conferidos, setConferidos] = useState([]);

  useEffect(() => {
    if (pedido) {
      fetch(`http://localhost:8000/produtos/${pedido.numero}`)
        .then((res) => res.json())
        .then((data) => setProdutos(data));
    }
  }, [pedido]);

  const conferirProduto = () => {
    if (!codigoBarras) return;

    const produtoEncontrado = produtos.find((produto) => produto.ptc === codigoBarras);
    
    if (!produtoEncontrado) {
      alert("Código de barras não encontrado!");
      return;
    }

    fetch("http://localhost:8000/atualizar_conferencia", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prefaturamento: pedido.numero,
        ptc: codigoBarras,
        quantidade_conferida: 1,
      }),
    })
    .then((res) => res.json())
    .then(() => {
      setConferidos([...conferidos, produtoEncontrado]);
      alert("Produto conferido com sucesso!");
      setCodigoBarras("");
    });
  };

  const finalizarConferencia = () => {
    fetch("http://localhost:8000/finalizar_conferencia", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prefaturamento: pedido.numero }),
    })
    .then((res) => res.json())
    .then(() => {
      alert("Conferência finalizada com sucesso!");
      voltar();
    });
  };

  return (
    <div className="conferencia-container">
      <h1>Conferência do Pedido {pedido?.numero}</h1>
      <button onClick={voltar} className="voltar-btn">Voltar</button>

      <input
        type="text"
        value={codigoBarras}
        onChange={(e) => setCodigoBarras(e.target.value)}
        placeholder="Escaneie o código de barras"
        className="input-barras"
      />
      <button onClick={conferirProduto} className="confirmar-btn">Confirmar</button>

      <h2>Produtos a Conferir</h2>
      <ul className="produto-lista">
        {produtos
          .filter((produto) => !conferidos.includes(produto))
          .map((produto) => (
            <li key={produto.ptc} className="produto-item">
              {produto.produto} - {produto.cor} - {produto.tamanho} ({produto.quantidade})
            </li>
          ))}
      </ul>

      <h2>Produtos Conferidos</h2>
      <ul className="produto-lista conferidos">
        {conferidos.map((produto, index) => (
          <li key={index} className="produto-item conferido">
            {produto.produto} - {produto.cor} - {produto.tamanho} ({produto.quantidade})
          </li>
        ))}
      </ul>

      <button onClick={finalizarConferencia} className="finalizar-btn">Finalizar Conferência</button>
    </div>
  );
}

export default Conferencia;
