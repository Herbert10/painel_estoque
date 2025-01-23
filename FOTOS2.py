import fdb
import base64
import os

# Conexão com o banco de dados
database_path = 'C:/SYS/BASE/MILLENNIUM'
username = 'SYSDBA'
password = 'masterkey'

# Conectar ao banco de dados
con = fdb.connect(database=database_path, user=username, password=password)
cursor = con.cursor()

try:
    # Consulta SQL para extrair o BLOB da imagem
    produto_id = '6185'
    query = f"SELECT foto FROM fotos WHERE produto = {produto_id}"

    # Executar consulta
    cursor.execute(query)
    row = cursor.fetchone()

    if row and row[0]:
        foto_blob = row[0]
        # Converter o BLOB para base64
        foto_base64 = base64.b64encode(foto_blob).decode('utf-8')

        # Opcional: salvar a string base64 em um arquivo para verificação
        with open('C:/dados/foto_base64.txt', 'w') as file:
            file.write(foto_base64)

        print("Conversão para base64 concluída e salva em 'C:/dados/foto_base64.txt'")
    else:
        print("Nenhuma foto encontrada para o produto.")

finally:
    # Fechar conexões
    cursor.close()
    con.close()
