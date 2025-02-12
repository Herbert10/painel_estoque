import React, { useState } from "react";
import PedidoLista from "./components/PedidoLista";
import Conferencia from "./components/Conferencia";

function App() {
  const [pedidoSelecionado, setPedidoSelecionado] = useState(null);

  return (
    <div>
      {!pedidoSelecionado ? (
        <PedidoLista selecionarPedido={setPedidoSelecionado} />
      ) : (
        <Conferencia pedido={pedidoSelecionado} voltar={() => setPedidoSelecionado(null)} />
      )}
    </div>
  );
}

export default App;
