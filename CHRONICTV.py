import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import fdb
import pygame
from playsound import playsound

# Configurações das cores da empresa
COR_FUNDO = 'black'
COR_TEXTO = 'white'

# Pasta onde as imagens e vídeos estão salvos
output_dir = r'C:\Painel'
video_dir = os.path.join(output_dir, 'video')  # Caminho da pasta de vídeos

# Lista de IPs para tentativa de conexão
ips = ['201.55.163.198', '10.10.0.167']

# Parâmetros de conexão com o banco de dados
con_params = {
    'host': '',  # Será definido dinamicamente
    'database': r'd:\SYS\BASE\MILLENIUM',
    'user': 'SYSDBA',
    'password': 'masterkey',
    'charset': 'ISO8859_1'
}

# Consulta SQL
sql_query = """
SELECT C.NOME AS CLIENTE, PV.COD_PEDIDOV as PEDIDO, PV.QUANTIDADE AS PECAS,
       F.NOME AS VENDEDOR, T.NOME AS TRANSPORTADORA
FROM PEDIDO_VENDA pv
LEFT OUTER JOIN CLIENTES c ON (PV.CLIENTE=C.CLIENTE)
LEFT OUTER JOIN FUNCIONARIOS f ON (PV.VENDEDOR=F.FUNCIONARIO)
LEFT OUTER JOIN TRANSPORTADORAS t ON (PV.TRANSPORTADORA=T.TRANSPORTADORA)
WHERE pv.TIPO_PEDIDO = 12000111 AND pv.EFETUADO = 'F' AND PV.DATA_EMISSAO  >= '04-24-2024'
"""

# Inicialização do Pygame para áudio
use_audio = True
try:
    pygame.mixer.init()
except pygame.error:
    print("Não foi possível inicializar o sistema de áudio com o Pygame.")
    use_audio = False  # Desativa as funcionalidades de áudio se falhar


# Função para buscar dados do banco de dados com tentativa de fallback nos IPs
def fetch_data():
    for ip in ips:
        con_params['host'] = ip
        try:
            with fdb.connect(**con_params) as con:
                cursor = con.cursor()
                cursor.execute(sql_query)
                rows = []
                for row in cursor.fetchall():
                    try:
                        formatted_row = [str(item, 'utf-8') if isinstance(item, bytes) else item for item in row]
                    except UnicodeDecodeError:
                        formatted_row = [str(item, 'latin1') if isinstance(item, bytes) else item for item in row]
                    formatted_row[2] = format(int(formatted_row[2]), ",d").replace(',', '.')
                    rows.append(tuple(formatted_row))
                return rows
        except fdb.DatabaseError:
            print(f"Falha na conexão com o IP: {ip}")
            continue

    # Se nenhum IP conectar, mostrar mensagem de erro e fechar o programa
    tk.messagebox.showerror("Erro de Conexão",
                            "Ligar para ALFA DASH (11) 94144-5959 e relatar que o IP não foi encontrado")
    root.destroy()  # Fecha a aplicação após a mensagem


# Função para atualizar os dados na tabela
def refresh_data(tree):
    global last_row_count
    for i in tree.get_children():
        tree.delete(i)
    data = fetch_data()
    if data:
        for row in data:
            tree.insert('', 'end', values=row)
        current_row_count = len(data)
        if current_row_count > last_row_count[0] and use_audio:
            try:
                pygame.mixer.music.load(r'C:\som\alerta.mp3')
                pygame.mixer.music.play()
            except pygame.error:
                playsound(r'C:\som\alerta.mp3')  # Usa playsound como backup
        last_row_count[0] = current_row_count


# Configuração da janela principal
root = tk.Tk()
root.title("Dashboard CHRONIC420")
root.configure(background=COR_FUNDO)
root.state('zoomed')

# Configuração do layout com frames e bordas
frame_top = tk.Frame(root, bg=COR_FUNDO)
frame_top.pack(side='top', fill='x')

frame_middle = tk.Frame(root, bg=COR_FUNDO)
frame_middle.pack(side='top', fill='x', expand=True)

frame_bottom_left = tk.Frame(frame_middle, bg=COR_FUNDO, width=2 * root.winfo_screenwidth() // 3,
                             highlightbackground="white", highlightthickness=1)
frame_bottom_left.pack(side='left', fill='both', expand=True)

frame_bottom_right = tk.Frame(frame_middle, bg=COR_FUNDO, width=root.winfo_screenwidth() // 3,
                              highlightbackground="white", highlightthickness=1)
frame_bottom_right.pack(side='right', fill='both', expand=True)


# Carrossel de Imagens
def exibir_carrossel():
    """
    Função para exibir o carrossel de imagens na parte verde.
    """
    # Carregar todas as imagens da pasta
    image_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.jpg')]

    # Verificar se há imagens para exibir
    if not image_files:
        print("Nenhuma imagem encontrada na pasta.")
        return

    print(f"Imagens carregadas: {image_files}")  # Debug para verificar as imagens carregadas

    # Função para exibir 3 imagens por vez para melhor visualização
    def show_images(start_index):
        for widget in frame_bottom_left.winfo_children():
            widget.destroy()
        for i in range(3):  # Exibir 3 imagens por vez
            index = (start_index + i) % len(image_files)
            try:
                img = Image.open(image_files[index])

                # Ajustar o tamanho das imagens para preencher o espaço do carrossel
                img_width, img_height = img.size
                max_width = frame_bottom_left.winfo_width() // 3  # Dividir pela quantidade de imagens
                max_height = frame_bottom_left.winfo_height()  # Altura total disponível
                scale = min(max_width / img_width, max_height / img_height)
                new_size = (int(img_width * scale), int(img_height * scale))
                img = img.resize(new_size, Image.LANCZOS)  # Corrigido para usar Image.LANCZOS

                img_tk = ImageTk.PhotoImage(img)
                img_label = tk.Label(frame_bottom_left, image=img_tk, bg=COR_FUNDO)
                img_label.image = img_tk
                img_label.pack(side='left', padx=10, pady=10, expand=True, fill='both')
            except Exception as e:
                print(f"Erro ao carregar imagem {image_files[index]}: {e}")

    start = 0

    def update_carousel():
        nonlocal start
        show_images(start)
        start += 3  # Incrementa por 3 para o próximo conjunto de imagens
        frame_bottom_left.after(5000, update_carousel)

    # Aguardar a janela ser renderizada para capturar o tamanho correto dos frames
    frame_bottom_left.after(1000, update_carousel)


# Função para exibir os vídeos em loop na parte azul
def exibir_videos():
    """
    Função para exibir vídeos na parte azul.
    """
    video_label = tk.Label(frame_bottom_right, bg=COR_FUNDO)
    video_label.pack(expand=True, fill='both')

    video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.mp4')]
    if not video_files:
        print("Nenhum vídeo encontrado na pasta.")
        return

    video_index = 0

    def play_video():
        nonlocal video_index
        cap = cv2.VideoCapture(video_files[video_index])
        video_index = (video_index + 1) % len(video_files)

        def stream():
            ret, frame = cap.read()
            if ret:
                # Redimensionar o vídeo para preencher o frame sem cortar
                frame_height, frame_width = frame.shape[:2]
                max_width = frame_bottom_right.winfo_width()
                max_height = frame_bottom_right.winfo_height()
                scale = min(max_width / frame_width, max_height / frame_height)
                new_size = (int(frame_width * scale), int(frame_height * scale))
                frame = cv2.resize(frame, new_size)

                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.config(image=imgtk)
                video_label.after(30, stream)
            else:
                cap.release()
                frame_bottom_right.after(6000, play_video)

        stream()

    # Aguardar a janela ser renderizada para capturar o tamanho correto dos frames
    frame_bottom_right.after(1000, play_video)


# Função para exibir a consulta ao banco de dados na parte vermelha
def exibir_consulta():
    """
    Função para exibir a tabela de dados na parte vermelha.
    """
    # Configuração do estilo do Treeview
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Treeview",
                    background=COR_FUNDO,
                    foreground=COR_TEXTO,
                    rowheight=35,
                    fieldbackground=COR_FUNDO,
                    font=('Helvetica', 22))
    style.configure("Treeview.Heading",
                    foreground=COR_TEXTO,
                    font=('Helvetica', 22),
                    background=COR_FUNDO)
    style.map('Treeview', background=[('selected', 'grey')])

    # Definindo as colunas do Treeview com ajustes nas larguras
    columns = ('CLIENTE', 'PEDIDO', 'PECAS', 'VENDEDOR', 'TRANSPORTADORA')
    tree = ttk.Treeview(frame_top, columns=columns, show='headings')

    # Ajustar as larguras das colunas para caber o conteúdo
    tree.heading('CLIENTE', text='CLIENTE')
    tree.column('CLIENTE', width=350, anchor='w')  # Largura ajustada para o nome completo do cliente

    tree.heading('PEDIDO', text='PEDIDO')
    tree.column('PEDIDO', width=150, anchor='center')

    tree.heading('PECAS', text='PECAS')
    tree.column('PECAS', width=80, anchor='center')

    tree.heading('VENDEDOR', text='VENDEDOR')
    tree.column('VENDEDOR', width=200, anchor='w')

    tree.heading('TRANSPORTADORA', text='TRANSPORTADORA')
    tree.column('TRANSPORTADORA', width=250, anchor='w')

    tree.pack(expand=True, fill='both')

    # Variável para armazenar a última quantidade de pedidos
    global last_row_count
    last_row_count = [0]

    # Atualizar os dados a cada 10 segundos
    def auto_refresh():
        refresh_data(tree)
        frame_top.after(10000, auto_refresh)  # Atualiza a cada 10 segundos

    auto_refresh()


# Executar todas as funções
exibir_carrossel()
exibir_videos()
exibir_consulta()

# Iniciar o loop principal do Tkinter
root.mainloop()
