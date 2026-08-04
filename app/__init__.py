import os
from flask import Flask
from dotenv import load_dotenv
from app.extensions import mail, csrf

load_dotenv()

# Caminho da raiz do projeto (onde fica o run.py), para manter templates/ e
# static/ exatamente nos mesmos lugares de antes da divisão em blueprints.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(_BASE_DIR, 'app', 'templates'),
        static_folder=os.path.join(_BASE_DIR, 'static'),
    )
    app.secret_key = os.getenv('SECRET_KEY')

    # --- CONFIGURAÇÕES DO FLASK-MAIL (GMAIL) ---
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = ('Controle Financeiro', os.getenv('MAIL_USERNAME'))

    mail.init_app(app)
    csrf.init_app(app)

    # --- REGISTRO DOS BLUEPRINTS ---
    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.transacoes import transacoes_bp
    from app.blueprints.categorias import categorias_bp
    from app.blueprints.contas import contas_bp
    from app.blueprints.perfil import perfil_bp
    from app.blueprints.relatorios import relatorios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transacoes_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(contas_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(relatorios_bp)

    return app
