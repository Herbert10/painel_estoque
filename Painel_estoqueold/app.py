from PIL import Image, ImageDraw, ImageFont
from tkinter import Tk, filedialog, messagebox
import os


def ajustar_foto_para_caixa(foto, caixa_largura, caixa_altura):
    """
    Ajusta a foto para caber proporcionalmente na caixa definida.
    """
    largura_foto, altura_foto = foto.size

    # Calcular a proporção da imagem
    proporcao_largura = caixa_largura / largura_foto
    proporcao_altura = caixa_altura / altura_foto
    proporcao = min(proporcao_largura, proporcao_altura)

    # Redimensionar a foto mantendo a proporção
    nova_largura = int(largura_foto * proporcao)
    nova_altura = int(altura_foto * proporcao)
    foto_redimensionada = foto.resize((nova_largura, nova_altura), Image.Resampling.LANCZOS)

    return foto_redimensionada


def criar_catalogo_com_template(template_path, fotos_selecionadas, output_path):
    """
    Cria um catálogo utilizando um template PNG como base, com fotos ajustadas proporcionalmente
    às caixas do template.
    """
    paginas = []
    template = Image.open(template_path).convert("RGBA")

    # Fonte para o texto (opcional: personalize com um arquivo .ttf)
    font = ImageFont.load_default()

    # Tamanho do template
    largura_template, altura_template = template.size

    # Definir posições exatas para fotos e textos
    posicoes = [
        {"x": 100, "y": 100, "width": 200, "height": 200},  # Espaço 1
        {"x": 400, "y": 100, "width": 200, "height": 200},  # Espaço 2
        {"x": 100, "y": 400, "width": 200, "height": 200},  # Espaço 3
        {"x": 400, "y": 400, "width": 200, "height": 200},  # Espaço 4
    ]

    # Adicionar produtos ao template
    for i, foto_path in enumerate(fotos_selecionadas):
        if i % len(posicoes) == 0:
            if i > 0:
                paginas.append(template.copy())  # Salva a página atual
            template = Image.open(template_path).convert("RGBA")  # Reinicia o template

        # Abrir a foto com fundo transparente
        foto = Image.open(foto_path).convert("RGBA")

        # Redimensionar a foto para caber na caixa
        caixa = posicoes[i % len(posicoes)]
        foto_ajustada = ajustar_foto_para_caixa(foto, caixa["width"], caixa["height"])

        # Calcular a posição centralizada da foto dentro da caixa
        x_centralizado = caixa["x"] + (caixa["width"] - foto_ajustada.size[0]) // 2
        y_centralizado = caixa["y"] + (caixa["height"] - foto_ajustada.size[1]) // 2

        # Colar a foto no template
        template.paste(foto_ajustada, (x_centralizado, y_centralizado), mask=foto_ajustada)

        # Inserir o nome do produto
        draw = ImageDraw.Draw(template)
        nome_produto = os.path.basename(foto_path).split('.')[0]
        draw.text((caixa["x"], caixa["y"] + caixa["height"] + 10), nome_produto, fill="black", font=font)

    # Adiciona a última página
    paginas.append(template)

    # Salvar em PDF
    paginas[0].save(
        output_path, save_all=True, append_images=paginas[1:], resolution=100
    )
    messagebox.showinfo("Sucesso", f"Catálogo gerado em: {output_path}")


# Interface gráfica para seleção de arquivos
def selecionar_template_e_fotos():
    root = Tk()
    root.withdraw()

    # Selecionar o template
    template_path = filedialog.askopenfilename(
        title="Selecione o template em PNG",
        filetypes=[("Imagens PNG", "*.png")]
    )
    if not template_path:
        messagebox.showwarning("Atenção", "Nenhum template foi selecionado.")
        return

    # Selecionar as fotos
    fotos_selecionadas = filedialog.askopenfilenames(
        title="Selecione as fotos dos produtos",
        filetypes=[("Imagens", "*.png *.jpg *.jpeg")]
    )
    if not fotos_selecionadas:
        messagebox.showwarning("Atenção", "Nenhuma foto foi selecionada.")
        return

    # Escolher onde salvar o PDF
    output_path = filedialog.asksaveasfilename(
        title="Salvar catálogo como",
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")]
    )
    if not output_path:
        messagebox.showwarning("Atenção", "Nenhum local de salvamento foi escolhido.")
        return

    # Criar o catálogo
    criar_catalogo_com_template(template_path, fotos_selecionadas, output_path)


# Executar o programa
if __name__ == "__main__":
    selecionar_template_e_fotos()
