// scripts.js - Funções JavaScript para a interação do formulário
document.addEventListener("DOMContentLoaded", function () {
    const forms = document.querySelectorAll(".rating-form");
    forms.forEach(form => {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData(form);
            const productId = formData.get("produto_id");

            fetch("/seller", {
                method: "POST",
                body: formData
            }).then(response => {
                if (response.ok) {
                    document.getElementById("produto-" + productId).remove();
                    alert("Avaliação salva com sucesso!");
                } else {
                    alert("Erro ao salvar a avaliação.");
                }
            });
        });
    });
});
