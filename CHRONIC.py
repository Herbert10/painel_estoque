import fdb
import tkinter as tk
from tkinter import ttk
import pygame
from playsound import playsound
import webview

# Configuração do IP fixo para conexão com o banco de dados
con_params = {
    'host': '201.55.163.198',  # Utilize o IP desejado
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
            formatted_row = [str(item, 'utf-8') if isinstance(item, bytes) else item for item in row]
            formatted_row[2] = format(int(formatted_row[2]), ",d").replace(',', '.')
            rows.append(tuple(formatted_row))
        return rows


def refresh_data(tree):
    global show_html, last_row_count
    data = fetch_data()
    for i in tree.get_children():
        tree.delete(i)
    for row in data:
        tree.insert('', 'end', values=row)
    current_row_count = len(data)

    # Alterna entre mostrar pedidos e HTML
    if show_html:
        hide_browser()
    else:
        show_browser()
    show_html = not show_html


def show_browser():
    # Configurações do JavaScript para focar no carrossel
    js_code = """
    document.querySelectorAll('body > *:not(.main-carousel)').forEach(el => el.style.display = 'none');
    document.querySelector('.main-carousel').style.marginTop = '0px'; // Ajusta a posição do carrossel
    """

    webview.create_window("Carrossel de Lançamentos", "https://www.chronic420.com.br/", width=800, height=600)
    webview.start(lambda: webview.windows[0].eval(js_code))  # Injetando o JavaScript após carregar


def hide_browser():
    # Lógica para esconder ou fechar o navegador se necessário
    # No pywebview, normalmente o navegador é fechado automaticamente
    pass


# Configuração da janela Tkinter
root = tk.Tk()
root.title("Dados Liberados para Entrega")
root.geometry('800x600')

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

# Variável para alternar entre exibição de pedidos e HTML
show_html = False
last_row_count = [0]


# Atualizar os dados a cada 10 segundos
def auto_refresh():
    refresh_data(tree)
    root.after(10000, auto_refresh)  # Atualiza a cada 10 segundos


auto_refresh()
root.mainloop()
