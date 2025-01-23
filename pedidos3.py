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

# Dicionário para armazenar as vendas por vendedor
vendas_por_vendedor = {}

# Data do último anúncio para evitar múltiplas execuções
ultimo_anuncio = None


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
                pygame.mixer.music.stop()
                break
            time.sleep(0.1)

        pygame.mixer.music.unload()
        os.remove(temp_file)


def verificar_hora_e_anunciar():
    global vendas_por_vendedor, ultimo_anuncio
    agora = datetime.now()
    if agora.hour == 17 and agora.minute == 0 and (ultimo_anuncio != agora.date()):
        if vendas_por_vendedor:
            vendedor_top = max(vendas_por_vendedor, key=vendas_por_vendedor.get)
            audio_url = f"https://megatoon.com.br/audio/{vendedor_audio_map[vendedor_top]}"
            play_sound_from_url(audio_url)
            vendas_por_vendedor.clear()
            ultimo_anuncio = agora.date()
        else:
            print("Nenhuma venda registrada hoje.")


def check_new_orders():
    global processed_orders
    cur = con.cursor()
    try:
        today = datetime.today().strftime('%Y-%m-%d')
        base_url = "https://megatoon.com.br/audio/"
        query = "SELECT pv.pedidov, pv.cod_pedidov, pv.tipo_pedido, ff.nome, pv.vendedor, pv.total FROM pedido_venda pv LEFT OUTER JOIN funcionarios ff ON pv.vendedor = ff.funcionario WHERE pv.efetuado='F' AND pv.filial<>19 AND pv.tipo_pedido in (3,5,4,29) AND pv.data_emissao = ?"
        cur.execute(query, (today,))
        for row in cur.fetchall():
            pedidov_id, vendedor, total_venda = row[0], row[4], row[5]
            if pedidov_id not in processed_orders:
                if vendedor in vendas_por_vendedor:
                    vendas_por_vendedor[vendedor] += total_venda
                else:
                    vendas_por_vendedor[vendedor] = total_venda
                processed_orders.append(pedidov_id)
    finally:
        cur.close()


# Mapeamento de vendedor para URL do áudio especial de fim de dia
vendedor_audio_map = {
    14: "sergio1.mp3",
    20596: "Alanis1.mp3",
    47: "Amanda1.mp3",
    12: "Edson1.mp3",
    393: "Carol1.mp3",
    5: "Lucas1.mp3",
    20623: "thissiane1.mp3",
    20627: "luiz1.mp3"
}

# Loop principal para verificar os pedidos e anunciar o vendedor top às 17:00
while True:
    check_new_orders()
    verificar_hora_e_anunciar()
    time.sleep(3)  # Executa a verificação a cada 3 segundos
