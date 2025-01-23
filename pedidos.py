import fdb
import time
import pygame
import os
import cv2
from datetime import datetime
import sys

# Inicializa o pygame para reprodução de som
pygame.init()
pygame.mixer.init()

# Define um evento personalizado para terminar a música
MUSIC_END = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(MUSIC_END)

# Conexão com o banco de dados Firebird
con = fdb.connect(dsn='MILLENIUMFLEXMETAL.DDNS.NET:c:/sys/base/millennium', user='SYSDBA', password='masterkey')

# Lista para guardar os IDs dos pedidos já processados
processed_orders = []

def play_sound(filename, duration=None):
    if not os.path.isfile(filename):
        print(f"Arquivo de áudio não encontrado: {filename}")
        return
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    start_time = time.time()
    # Loop para verificar se o tempo de reprodução especificado foi atingido
    while pygame.mixer.music.get_busy():
        if duration and (time.time() - start_time > duration):
            pygame.mixer.music.stop()
            break
        for event in pygame.event.get():
            if event.type == MUSIC_END:
                break
        time.sleep(0.1)  # Reduz a carga de CPU

def play_video_with_sound(filename):
    cap = cv2.VideoCapture(filename)
    pygame.mixer.quit()  # Fecha o mixer para liberar o dispositivo de áudio

    cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Video", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        screen_width, screen_height = cv2.getWindowImageRect("Video")[2], cv2.getWindowImageRect("Video")[3]
        frame_height, frame_width = frame.shape[:2]

        aspect_ratio_frame = frame_width / frame_height
        aspect_ratio_screen = screen_width / screen_height

        if aspect_ratio_screen > aspect_ratio_frame:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio_frame)
        else:
            new_width = screen_width
            new_height = int(new_width / aspect_ratio_frame)

        resized_frame = cv2.resize(frame, (new_width, new_height))
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2

        fullscreen_frame = cv2.copyMakeBorder(
            resized_frame, y_offset, screen_height - new_height - y_offset,
            x_offset, screen_width - new_width - x_offset,
            cv2.BORDER_CONSTANT, value=[0, 0, 0]
        )

        cv2.imshow('Video', fullscreen_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    pygame.mixer.init()  # Reinicializa o mixer

def display_slideshow(image_folder):
    images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]
    if not images:
        print("Nenhuma imagem encontrada na pasta:", image_folder)
        return

    cv2.namedWindow("Slideshow", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Slideshow", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    current_image = 0
    while True:
        img = cv2.imread(images[current_image])
        screen_width, screen_height = cv2.getWindowImageRect("Slideshow")[2], cv2.getWindowImageRect("Slideshow")[3]
        frame_height, frame_width = img.shape[:2]

        aspect_ratio_frame = frame_width / frame_height
        aspect_ratio_screen = screen_width / screen_height

        if aspect_ratio_screen > aspect_ratio_frame:
            new_height = screen_height
            new_width = int(new_height * aspect_ratio_frame)
        else:
            new_width = screen_width
            new_height = int(new_width / aspect_ratio_frame)

        resized_frame = cv2.resize(img, (new_width, new_height))
        x_offset = (screen_width - new_width) // 2
        y_offset = (screen_height - new_height) // 2

        fullscreen_frame = cv2.copyMakeBorder(
            resized_frame, y_offset, screen_height - new_height - y_offset,
            x_offset, screen_width - new_width - x_offset,
            cv2.BORDER_CONSTANT, value=[0, 0, 0]
        )

        cv2.imshow('Slideshow', fullscreen_frame)
        if cv2.waitKey(3000) & 0xFF == ord('q'):  # Exibe cada imagem por 3 segundos
            break

        current_image = (current_image + 1) % len(images)

        # Verifica se há algum pedido novo a cada ciclo
        if check_new_orders():
            break

        if cv2.waitKey(1) & 0xFF == 27:  # Verifica se a tecla ESC foi pressionada
            sys.exit()

    cv2.destroyAllWindows()

def check_new_orders():
    global processed_orders
    cur = con.cursor()
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        # Realiza a query para cada uma das condições
        queries = [
            ("SELECT pv.pedidov, pv.cod_pedidov, pv.tipo_pedido, ff.nome, pv.vendedor FROM pedido_venda pv LEFT OUTER JOIN funcionarios ff ON pv.vendedor = ff.funcionario WHERE pv.efetuado='F' AND pv.filial<>19 AND pv.tipo_pedido in (3,5,4,29) AND pv.data_emissao = ?", 'v1'),
        ]

        for query, version in queries:
            cur.execute(query, (today,))
            for row in cur.fetchall():
                pedidov_id = row[0]  # Assumindo que o ID do pedido é a primeira coluna
                if pedidov_id not in processed_orders:
                    vendedor = row[4]
                    # Escolhe o áudio baseado no vendedor e na versão
                    vendedor_audio_map = {
                        14: "Sergio",
                        20596: "Alanis",
                        47: "Amanda",
                        12: "Edson",
                        393: "Carol",
                        5: "Lucas",
                        20623: "Thissiane",
                        75: "Roberto",
                        20633: "Vinicius",
                        20590: "Mercado_Livre",
                        51: "Grasi",
                        29: "Giovana",
                        20627: "Geison",
                        490: "e-commerce",
                        491: "Bruna",
                        206222: "Amy",
                        20629: "Kymberly"
                    }
                    if vendedor in vendedor_audio_map:
                        version_filename = os.path.join("c:\\audio", "v1.mp3")
                        play_sound(version_filename, 5)  # Reproduz apenas os primeiros 5 segundos do áudio da versão
                        time.sleep(2)  # Espera 2 segundos após o áudio
                        vendedor_audio_filename = os.path.join("c:\\audio", f"{vendedor_audio_map[vendedor]}.mp3")
                        play_sound(vendedor_audio_filename)  # Reproduz o áudio do vendedor
                        aplausos_filename = os.path.join("c:\\audio", "aplausos.mp3")
                        play_sound(aplausos_filename)  # Reproduz o áudio de aplausos
                        video_filename = os.path.join("c:\\audio", f"{vendedor_audio_map[vendedor]}.mov")
                        play_video_with_sound(video_filename)  # Reproduz o vídeo do vendedor
                    processed_orders.append(pedidov_id)
                    return True  # Indica que um novo pedido foi processado
    finally:
        cur.close()
    return False  # Indica que nenhum novo pedido foi encontrado

# Loop para verificar os pedidos a cada 3 segundos
while True:
    if not check_new_orders():
        display_slideshow("C:\\audio\\Imagens")
    if cv2.waitKey(1) & 0xFF == 27:  # Verifica se a tecla ESC foi pressionada
        break
    time.sleep(3)
pygame.quit()
cv2.destroyAllWindows()
sys.exit()
