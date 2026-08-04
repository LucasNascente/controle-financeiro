import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # FLASK_DEBUG=true no seu .env liga o modo debug localmente.
    # Em produção, NUNCA deixe isso ligado (permite execução de código
    # arbitrário se o servidor for exposto publicamente).
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)
