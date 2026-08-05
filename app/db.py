import os
import tempfile
import mysql.connector
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

_caminho_certificado_temporario = None


def _resolver_caminho_certificado_ssl():
    """Aiven (e a maioria dos bancos gerenciados na nuvem) exige conexão via
    SSL e fornece um certificado (ca.pem). Suportamos duas formas de
    configurar isso:

    - DB_SSL_CA: caminho pra um arquivo .pem já existente no servidor
      (ex: um "Secret File" do Render).
    - DB_SSL_CA_CONTENT: o conteúdo do certificado direto numa variável de
      ambiente (útil quando a plataforma de hospedagem não tem upload de
      arquivo fácil) — nesse caso, escrevemos o conteúdo num arquivo
      temporário na primeira vez que a conexão é aberta.
    """
    global _caminho_certificado_temporario

    caminho_direto = os.getenv('DB_SSL_CA')
    if caminho_direto:
        return caminho_direto

    conteudo_certificado = os.getenv('DB_SSL_CA_CONTENT')
    if conteudo_certificado:
        if _caminho_certificado_temporario is None:
            arquivo_temp = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
            arquivo_temp.write(conteudo_certificado)
            arquivo_temp.close()
            _caminho_certificado_temporario = arquivo_temp.name
        return _caminho_certificado_temporario

    return None


def get_db_connection():
    conexao_kwargs = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'controle_financeiro'),
    }

    # Em ambiente local com MySQL na sua máquina, nenhuma das variáveis de
    # SSL existe no .env, e a conexão continua funcionando sem SSL, como
    # sempre funcionou.
    caminho_certificado_ssl = _resolver_caminho_certificado_ssl()
    if caminho_certificado_ssl:
        conexao_kwargs['ssl_ca'] = caminho_certificado_ssl
        conexao_kwargs['ssl_verify_cert'] = True

    return mysql.connector.connect(**conexao_kwargs)