import fdb
import time
import pygame
import vlc
from datetime import datetime
from pywinauto.application import Application
import pygetwindow as gw
import cv2
import os

# Caminho para a instalação do VLC
vlc_path = os.path.abspath("vlc_libs")

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

def play_sound(filename, duration=5):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    start_time = time.time()
    # Loop para verificar se o tempo de reprodução especificado foi atingido
    while pygame.mixer.music.get_busy():
        if time.time() - start_time > duration:
            pygame.mixer.music.stop()
            break
        for event in pygame.event.get():
            if event.type == MUSIC_END:
                break
        time.sleep(0.1)  # Reduz a carga de CPU
    pygame.mixer.quit()  # Reinicializa o mixer para evitar problemas com o dispositivo de áudio
    pygame.mixer.init()

def bring_vlc_to_front():
    for _ in range(10):  # Tenta por 10 vezes
        time.sleep(1)  # Espera um segundo para garantir que a janela do VLC seja criada
        try:
            windows = gw.getWindowsWithTitle('VLC media player')
            if windows:
                window = windows[0]
                window.activate()
                window.maximize()
                break
        except Exception as e:
            print(f"Erro ao trazer a janela do VLC para frente: {e}")
    else:
        print("Janela do VLC não encontrada.")

def play_video_with_sound(filename):
    vlc_instance = vlc.Instance('--no-xlib --no-embedded-video')
    player = vlc_instance.media_player_new()
    media = vlc_instance.media_new(filename)
    player.set_media(media)
    player.set_fullscreen(True)
    player.play()

    # Trazer a janela do VLC para frente
    bring_vlc_to_front()

    while True:
        state = player.get_state()
        if state in [vlc.State.Ended, vlc.State.Error]:
            break
        time.sleep(0.1)

    player.stop()

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
                        14: "sergio",
                        20596: "Alanis",
                        47: "Amanda",
                        12: "Edson",
                        393: "Carol",
                        5: "Lucas",
                        20623: "thissiane",
                        20627: "luiz"
                    }
                    if vendedor in vendedor_audio_map:
                        version_filename = f"c:\\audio\\v1.mp3"
                        play_sound(version_filename, 5)  # Reproduz apenas os primeiros 5 segundos do áudio da versão
                        time.sleep(2)  # Espera 2 segundos após o áudio
                        video_filename = f"c:\\audio\\{vendedor_audio_map[vendedor]}.mov"
                        play_video_with_sound(video_filename)  # Reproduz o vídeo do vendedor
                    processed_orders.append(pedidov_id)
    finally:
        cur.close()

# Loop para verificar os pedidos a cada 3 segundos
while True:
    check_new_orders()
    time.sleep(3)
