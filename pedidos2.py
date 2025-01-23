import fdb
import time
import pygame
import requests
import os
from datetime import datetime

# Inicializa o pygame para reprodução de som
pygame.init()
pygame.mixer.init()

# Conexão com o banco de dados Firebird
con = fdb.connect(dsn='MILLENIUMFLEXMETAL.DDNS.NET:c:/sys/base/millennium', user='SYSDBA', password='masterkey')

# Lista para guardar os IDs dos pedidos já processados
processed_orders = []


def play_sound_from_url(url, duration=5):
    response = requests.get(url)
    if response.status_code == 200:
        # Salva o arquivo de áudio temporariamente
        temp_file = "temp_audio.mp3"
        with open(temp_file, "wb") as f:
            f.write(response.content)

        # Carrega e reproduz o áudio
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        # Espera pela duração especificada ou até a música terminar
        start_time = time.time()
        while pygame.mixer.music.get_busy():
            current_time = time.time()
            if current_time - start_time >= duration:
                pygame.mixer.music.stop()  # Interrompe a música explicitamente
                break
            time.sleep(0.1)  # Aguarda um breve momento para não sobrecarregar o loop

        pygame.mixer.music.unload()  # Libera o recurso de música

        # Tenta remover o arquivo temporário
        try:
            os.remove(temp_file)  # Remove o arquivo temporário após a reprodução
        except PermissionError as e:
            print(f"Erro ao tentar remover o arquivo temporário: {e}")


def check_new_orders():
    global processed_orders
    cur = con.cursor()
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        base_url = "https://megatoon.com.br/audio/"
        queries = [
            (
            "SELECT pv.pedidov, pv.cod_pedidov, pv.tipo_pedido, ff.nome, pv.vendedor FROM pedido_venda pv LEFT OUTER JOIN funcionarios ff ON pv.vendedor = ff.funcionario WHERE pv.efetuado='F' AND pv.filial<>19 AND pv.tipo_pedido in (3,5,4,29) AND pv.total >= 300 AND pv.total <= 1500 AND pv.data_emissao = ?",
            'v1.mp3'),
            (
            "SELECT pv.pedidov, pv.cod_pedidov, pv.tipo_pedido, ff.nome, pv.vendedor FROM pedido_venda pv LEFT OUTER JOIN funcionarios ff ON pv.vendedor = ff.funcionario WHERE pv.efetuado='F' AND pv.filial<>19 AND pv.tipo_pedido in (3,5,4,29) AND pv.total >= 1501 AND pv.total <= 3000 AND pv.data_emissao = ?",
            'v2.mp3'),
            (
            "SELECT pv.pedidov, pv.cod_pedidov, pv.tipo_pedido, ff.nome, pv.vendedor FROM pedido_venda pv LEFT OUTER JOIN funcionarios ff ON pv.vendedor = ff.funcionario WHERE pv.efetuado='F' AND pv.filial<>19 AND pv.tipo_pedido in (3,5,4,29) AND pv.total >= 3001 AND pv.data_emissao = ?",
            'v3.mp3')
        ]
        vendedor_audio_map = {
            14: "Sergio.mp3",
            20596: "Alanis.mp3",
            47: "Amanda.mp3",
            12: "Edson.mp3",
            393: "Carol.mp3",
            5: "Lucas.mp3",
            20623: "Thissiane.mp3",
            20627: "Luiz.mp3"
        }

        for query, version in queries:
            cur.execute(query, (today,))
            for row in cur.fetchall():
                pedidov_id = row[0]
                if pedidov_id not in processed_orders:
                    vendedor = row[4]
                    if vendedor in vendedor_audio_map:
                        audio_url = f"{base_url}{vendedor_audio_map[vendedor]}"
                        version_url = f"{base_url}{version}"
                        play_sound_from_url(audio_url)  # Reproduz o áudio do vendedor
                        play_sound_from_url(version_url,
                                            5)  # Reproduz apenas os primeiros 5 segundos do áudio da versão
                    processed_orders.append(pedidov_id)
    finally:
        cur.close()


# Loop para verificar os pedidos a cada 3 segundos
while True:
    check_new_orders()
    time.sleep(3)
