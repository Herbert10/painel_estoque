import React, { useState, useEffect } from "react";
import "./styles.css";

function PedidoLista({ selecionarPedido }) {
  const [pedidos, setPedidos] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/pedidos")
      .then((res) => res.json())
      .then((data) => setPedidos(data));
  }, []);

  return (
    <div>
      <h1>Pedidos Pendentes</h1>
      <ul className="pedido-lista">
        {pedidos.map((pedido) => (
          <li key={pedido.numero} className="pedido-item" onClick={() => selecionarPedido(pedido)}>
            <strong>Pedido:</strong> {pedido.numero} - {pedido.nome_cliente}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PedidoLista;
