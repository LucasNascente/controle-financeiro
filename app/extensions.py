import os
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# Garante que o .env já foi carregado antes de ler SECRET_KEY abaixo,
# independente da ordem em que este módulo for importado por outro arquivo.
load_dotenv()

# Instância única, compartilhada por todos os blueprints.
# csrf é "ligada" à aplicação de verdade em app/__init__.py (init_app).
csrf = CSRFProtect()

# O serializer usado para gerar/validar o token de recuperação de senha
# só depende da SECRET_KEY (não do objeto app em si), então pode ser
# criado uma única vez aqui e importado por quem precisar.
serializer = URLSafeTimedSerializer(os.getenv('SECRET_KEY'))
