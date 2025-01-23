import os
import tkinter as tk
from PIL import Image, ImageTk
import cv2

# Pasta onde as imagens e vídeos estão salvos
output_dir = r'C:\Painel'
video_dir = os.path.join(output_dir, 'video')  # Caminho da pasta de vídeos

def exibir_carrossel():
    """
    Função para exibir as imagens em um carrossel com Tkinter e reproduzir vídeos de forma intercalada usando OpenCV.
    """
    root = tk.Tk()
    root.title("Carrossel de Lançamentos")

    # Configurações da janela
    frame = tk.Frame(root)
    frame.pack(expand=True, fill='both')

    # Carregar todas as imagens da pasta
    image_files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.jpg')]

    # Carregar todos os vídeos da pasta
    video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith('.mp4')]

    # Verifica se há imagens e vídeos na pasta
    if not image_files:
        print("Nenhuma imagem encontrada na pasta.")
        return

    if not video_files:
        print("Nenhum vídeo encontrado na pasta.")
        return

    # Inicializar o carrossel na primeira imagem e vídeo
    start = 0
    video_index = 0

    # Função para exibir 4 imagens por vez
    def show_images(start_index):
        # Limpar o frame antes de exibir novas imagens
        for widget in frame.winfo_children():
            widget.destroy()

        # Exibir 4 imagens por vez, repetindo se necessário
        for i in range(4):
            index = (start_index + i) % len(image_files)  # Usa o módulo para repetir ciclicamente
            img = Image.open(image_files[index])
            img.thumbnail((200, 200))  # Ajustar o tamanho das imagens
            img_tk = ImageTk.PhotoImage(img)

            # Criar um frame para imagem e texto
            img_frame = tk.Frame(frame)
            img_frame.grid(row=0, column=i, padx=10, pady=10)

            # Adicionar a imagem
            label_img = tk.Label(img_frame, image=img_tk)
            label_img.image = img_tk
            label_img.pack()

            # Adicionar o nome do produto (usando o nome do arquivo como referência)
            nome_produto = os.path.basename(image_files[index]).replace('.jpg', '').replace('_', ' ')
            label_nome = tk.Label(img_frame, text=nome_produto, wraplength=200, justify='center')
            label_nome.pack()

    # Função para exibir o vídeo usando OpenCV
    def show_video():
        nonlocal video_index
        # Limpar o frame antes de exibir o vídeo
        for widget in frame.winfo_children():
            widget.destroy()

        # Selecionar o vídeo atual
        current_video = video_files[video_index]
        video_index = (video_index + 1) % len(video_files)  # Alternar para o próximo vídeo

        # Criar um label para exibir o vídeo
        video_label = tk.Label(frame)
        video_label.pack(expand=True, fill='both')

        # Função para reproduzir o vídeo por 6 segundos
        def play_video():
            cap = cv2.VideoCapture(current_video)
            start_time = root.after(6000, lambda: (cap.release(), stop_video_and_return_to_carousel()))  # Define para parar o vídeo após 6 segundos

            def stream():
                ret, frame = cap.read()
                if ret:
                    # Converter o frame do OpenCV (BGR) para Tkinter (RGB)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    video_label.imgtk = imgtk
                    video_label.config(image=imgtk)
                    video_label.after(30, stream)  # Chama o próximo frame
                else:
                    cap.release()
                    root.after_cancel(start_time)  # Cancela o tempo de espera se o vídeo terminar antes dos 6 segundos
                    stop_video_and_return_to_carousel()  # Volta para o carrossel

            stream()

        play_video()

    def stop_video_and_return_to_carousel():
        # Limpar o frame e retornar ao carrossel de imagens
        for widget in frame.winfo_children():
            widget.destroy()
        next_images()  # Reinicia o carrossel de imagens

    def next_images():
        nonlocal start
        start += 4
        show_images(start)
        root.after(5000, update_carousel)  # Configura para atualizar o carrossel a cada 5 segundos

    # Alterna entre o carrossel e o vídeo a cada 3 ciclos
    def update_carousel():
        if (start // 4) % 3 == 2:  # Exibe o vídeo a cada 3 ciclos do carrossel
            show_video()
        else:
            next_images()

    show_images(start)  # Inicializa exibindo imagens
    root.after(5000, update_carousel)  # Inicia a primeira atualização após 5 segundos
    root.mainloop()

# Executar a função para exibir o carrossel
exibir_carrossel()
