# Guia de Deploy — Controle Financeiro (Render + Aiven MySQL)

Este guia parte do princípio de que seu código já está no GitHub, atualizado
com as mudanças desta conversa (Gunicorn, `Procfile`, suporte a SSL no banco).

---

## Parte 1 — Criar o banco de dados (Aiven MySQL, grátis)

1. Crie uma conta em **https://aiven.io** (não pede cartão de crédito).
2. No painel, clique em **Create service** → escolha **MySQL**.
3. Selecione o plano **Free**.
4. Escolha uma região (qualquer uma próxima do Brasil, ex: `aws-us-east-1` ou
   a mais próxima disponível no free tier).
5. Dê um nome ao serviço (ex: `controle-financeiro-db`) e crie.
6. Aguarde alguns minutos até o status mudar para **Running**.
7. Na aba **Overview** do serviço, você verá os dados de conexão:
   - `Host`
   - `Port` (não é 3306, é uma porta específica do Aiven)
   - `User` (geralmente `avnadmin`)
   - `Password`
   - Um botão pra baixar o certificado **CA Certificate** (`ca.pem`) — baixe esse arquivo, você vai precisar dele.
8. Ainda no painel, crie o banco de dados de verdade (schema) chamado
   `controle_financeiro` (aba **Databases** → **Create database**).
9. Recrie as tabelas nesse banco novo. Use o **console SQL** do próprio
   Aiven (aba **Query Editor / Console**) ou conecte com um cliente MySQL
   (ex: MySQL Workbench, DBeaver, ou linha de comando) usando os dados do
   passo 7, e rode os `CREATE TABLE` das suas tabelas atuais
   (`usuarios`, `categorias`, `contas`, `transacoes`).

> Se você não tiver mais o script de criação das tabelas salvo, use um
> cliente MySQL local pra exportar a estrutura do seu banco atual
> (`mysqldump --no-data`) e importe essa estrutura no Aiven.

---

## Parte 2 — Publicar o código (Render, grátis)

1. Crie uma conta em **https://render.com** (dá pra entrar direto com GitHub).
2. Clique em **New** → **Web Service**.
3. Conecte seu repositório `controle-financeiro`.
4. Configure:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Instance Type**: Free
5. Antes de clicar em "Create", role até **Environment Variables** e
   adicione (usando os dados que você pegou do Aiven na Parte 1):

   | Variável | Valor |
   |---|---|
   | `SECRET_KEY` | uma string aleatória longa (gere uma nova, não reuse a local) |
   | `FLASK_DEBUG` | `false` |
   | `DB_HOST` | host do Aiven |
   | `DB_PORT` | porta do Aiven |
   | `DB_USER` | usuário do Aiven (ex: `avnadmin`) |
   | `DB_PASSWORD` | senha do Aiven |
   | `DB_NAME` | `controle_financeiro` |
   | `MAIL_USERNAME` | seu e-mail do Gmail |
   | `MAIL_PASSWORD` | sua senha de app do Gmail |

6. Sobre o certificado SSL (`ca.pem` que você baixou do Aiven), escolha uma
   das duas formas — o código já suporta as duas:
   - **Mais simples no Render**: abra o `ca.pem` num editor de texto, copie
     todo o conteúdo, e cole numa variável de ambiente chamada
     `DB_SSL_CA_CONTENT`.
   - **Alternativa**: usar o recurso **Secret Files** do Render, subir o
     `ca.pem` lá, e apontar `DB_SSL_CA` pro caminho que o Render te dá
     (algo como `/etc/secrets/ca.pem`).
7. Clique em **Create Web Service**. O Render vai buildar e subir
   automaticamente. Depois disso, toda vez que você der `git push`, ele
   republica sozinho.

---

## Parte 3 — Gerar uma SECRET_KEY forte

Não reutilize a chave que você usa localmente. Gere uma nova só pra
produção, rodando isso no seu terminal:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Cole o resultado na variável `SECRET_KEY` do Render.

---

## Parte 4 — Testar

1. Acesse a URL que o Render te deu (algo como
   `https://controle-financeiro.onrender.com`).
2. A primeira visita depois de um tempo parado demora ~1 minuto pra
   "acordar" — isso é normal no plano gratuito, não é erro.
3. Crie uma conta de teste, faça login, cadastre uma transação, confira
   se o dashboard, categorias e contas funcionam.
4. Teste o "esqueci minha senha" pra confirmar que o e-mail está sendo
   enviado corretamente a partir do servidor (às vezes provedores de
   e-mail bloqueiam envios de IPs de datacenter — se não funcionar,
   me avise que investigamos).

---

## O que NÃO fazer

- Não deixe `FLASK_DEBUG=true` em produção (veja a conversa anterior sobre
  por que isso é um risco de segurança sério).
- Não commite o `.env` nem o `ca.pem` no Git — mantenha só como variáveis
  de ambiente / secret files na plataforma de hospedagem.
- Não use a mesma `SECRET_KEY` de desenvolvimento em produção.
