import os
import requests
from bs4 import BeautifulSoup

# URL do site
url = 'https://www.chronic420.com.br/'

# Pasta onde as imagens serão salvas
output_dir = r'C:\Painel'

# Criar a pasta se não existir
os.makedirs(output_dir, exist_ok=True)


def baixar_imagens_e_nomes_lancamentos(url):
    """
    Função para baixar imagens e nomes dos produtos da seção de lançamentos do carrossel no site.
    """
    # Fazendo a requisição para o site
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Parseando o HTML com BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrando a seção específica do carrossel de lançamentos
        carrossel = soup.find('div', class_='owl-container')

        # Verificando se encontrou a seção do carrossel
        if carrossel:
            # Encontrando todas as imagens dentro do carrossel
            imagens = carrossel.find_all('img')

            # Baixando cada imagem encontrada e capturando os nomes
            for index, img in enumerate(imagens):
                # Extrair o URL da imagem
                img_url = img['src']

                # Extrair o nome do produto a partir do atributo title
                nome_produto = img.get('title', f'Produto_{index + 1}')  # Usa um nome padrão se title não existir

                # Adicionando https se o URL for relativo
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url

                # Baixar a imagem
                try:
                    img_data = requests.get(img_url).content
                    # Substitui caracteres inválidos para nomes de arquivos
                    nome_arquivo = nome_produto.replace('/', '_').replace('\\', '_') + '.jpg'
                    img_path = os.path.join(output_dir, nome_arquivo)

                    # Salvando a imagem
                    with open(img_path, 'wb') as img_file:
                        img_file.write(img_data)

                    print(f'Imagem do produto "{nome_produto}" salva: {img_path}')

                except Exception as e:
                    print(f"Erro ao baixar a imagem do produto '{nome_produto}': {e}")
        else:
            print("Seção do carrossel com a classe 'owl-container' não encontrada.")
    else:
        print(f"Erro ao acessar o site: {response.status_code}")


# Executar a função para baixar as imagens e nomes dos produtos
baixar_imagens_e_nomes_lancamentos(url)
