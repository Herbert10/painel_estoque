import fdb
import tkinter as tk
from tkinter import ttk
import pygame
from playsound import playsound

# Tenta inicializar o mixer do Pygame e define uma flag para uso de áudio
use_audio = True
try:
    pygame.mixer.init()
except pygame.error:
    print("Não foi possível inicializar o sistema de áudio com o Pygame.")
    use_audio = False  # Desativa as funcionalidades de áudio se falhar

# Parâmetros de conexão com o banco de dados
con_params = {
    'host': '201.55.163.198',
    'database': r'd:\SYS\BASE\MILLENIUM',
    'user': 'SYSDBA',
    'password': 'masterkey',
    'charset': 'UTF8'
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

def fetch_data():
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

def refresh_data(tree):
    global last_row_count
    for i in tree.get_children():
        tree.delete(i)
    data = fetch_data()
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

# Configuração da janela Tkinter
root = tk.Tk()
root.title("Dados Liberados para Entrega")
root.configure(background='black')

# Configuração do estilo do Treeview
style = ttk.Style(root)
style.theme_use("clam")
style.configure("Treeview",
                background="black",
                foreground="white",
                rowheight=35,
                fieldbackground="black",
                font=('Helvetica', 22))
style.configure("Treeview.Heading",
                foreground='white',
                font=('Helvetica', 22),
                background='black')
style.map('Treeview', background=[('selected', 'grey')])

# Definindo as colunas do Treeview
columns = ('CLIENTE', 'PEDIDO', 'PECAS', 'VENDEDOR', 'TRANSPORTADORA')
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    if col == 'PECAS':
        tree.column(col, width=120, anchor='center')
tree.pack(expand=True, fill='both')

# Variável para armazenar a última quantidade de pedidos
last_row_count = [0]

# Atualizar os dados a cada 10 segundos
def auto_refresh():
    refresh_data(tree)
    root.after(10000, auto_refresh)  # Atualiza a cada 10 segundos

auto_refresh()

root.mainloop()
