# 💰 Controle Financeiro

Aplicação web para controle financeiro pessoal, desenvolvida em **Python** com o micro-framework **Flask** e banco de dados **MySQL**. Permite que cada usuário cadastre receitas e despesas, organize por categorias e contas, visualize um dashboard com gráficos, filtre por mês/ano, exporte relatórios em CSV e gerencie seu próprio perfil.

---

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias utilizadas](#-tecnologias-utilizadas)
- [Estrutura do projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e configuração](#-instalação-e-configuração)

---

## ✨ Funcionalidades

- **Autenticação de usuários**: cadastro, login e logout com senha criptografada.
- **Recuperação de senha por e-mail**: envio de link com token assinado e expiração de 30 minutos.
- **Dashboard financeiro**: totais de receitas, despesas e saldo do período, com dados prontos para gráfico de despesas por categoria.
- **Filtros por mês e ano** (incluindo opção "todos os meses"/"todos os anos") e busca por descrição da transação.
- **Cadastro de transações** (receitas e despesas), com categoria e conta associadas.
- **Edição e exclusão de transações**, sempre restritas ao dono do registro.
- **Categorias personalizadas** por usuário, com cor associada (usada no gráfico).
- **Contas**: uma conta padrão ("Carteira Principal") é criada automaticamente no cadastro.
- **Extrato / impressão**: tela de extrato por período, pronta para impressão/PDF.
- **Exportação para Excel (CSV)**: exportação com separador `;` e BOM UTF-8, para abrir corretamente acentos no Excel.
- **Perfil do usuário**: edição de nome, alteração de senha (com verificação da senha atual) e exclusão de conta (com remoção em cascata de transações, categorias e contas).
- **Categorias padrão automáticas no cadastro**: Alimentação, Moradia, Transporte, Lazer e Salário/Receita, cada uma com uma cor pré-definida.

## 🛠 Tecnologias utilizadas

| Categoria | Tecnologia |
|---|---|
| Linguagem | Python |
| Framework web | Flask |
| Banco de dados | MySQL (via `mysql-connector-python`) |
| Segurança de senha | Werkzeug (`generate_password_hash` / `check_password_hash`) |
| Proteção CSRF | Flask-WTF (`CSRFProtect`) |
| Envio de e-mail | Flask-Mail (SMTP do Gmail) |
| Tokens de recuperação de senha | itsdangerous (`URLSafeTimedSerializer`) |
| Configuração de ambiente | python-dotenv |
| Templates | Jinja2 |

Versões fixadas em `requirements.txt`:

```
blinker==1.9.0
click==8.4.2
colorama==0.4.6
Flask==3.1.3
Flask-Mail==0.10.0
Flask-WTF==1.3.0
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.3
mysql-connector-python==26.7.0
python-dotenv==1.2.2
Werkzeug==3.1.8
WTForms==3.2.2
```
## 📁 Estrutura do projeto

```
controle-financeiro/
├── app/                    # Pacote principal da aplicação
│   ├── db.py               # Conexão com o banco (get_db_connection) — não inspecionado
│   └── templates/          # Templates Jinja2 (login, cadastro, dashboard, etc.)
├── criar_usuario.py        # Script utilitário para criar/resetar um usuário admin
├── requirements.txt        # Dependências do projeto
├── run.py                  # Aplicação Flask (rotas, lógica de negócio)
└── .gitignore
```

## ✅ Pré-requisitos

- Python 3.10+ (recomendado)
- Servidor MySQL em execução, com um banco de dados criado para o projeto
- Uma conta do Gmail com **senha de app** gerada (para o envio de e-mails de recuperação de senha via SMTP)

## 🚀 Instalação e configuração

```bash
# 1. Clone o repositório
git clone https://github.com/LucasNascente/controle-financeiro.git
cd controle-financeiro

# 2. Crie e ative um ambiente virtual
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Crie o arquivo .env na raiz do projeto 

# 5. Crie as tabelas no MySQL

# 6. (Opcional) Crie um usuário administrador de teste
python criar_usuario.py

# 7. Rode a aplicação
python run.py
```

A aplicação deverá ficar disponível em `http://127.0.0.1:5000`.
