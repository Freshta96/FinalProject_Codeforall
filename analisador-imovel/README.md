# 🏘️ Analisador de Investimento Imobiliário

App de análise de investimento imobiliário em Portugal usando Inteligência Artificial.

## Funcionalidades

- Cálculo de yield bruta e líquida
- Cálculo de payback period
- Estimativa automática de renda mensal via IA
- Estimativa automática de despesas (condomínio, IMI, manutenção) via IA
- Análise qualitativa estruturada: preço/m², perfil de risco, red flags e veredicto
- Dropdown com todos os concelhos de Portugal continental

## Como correr

### 1. Clonar o repositório
```bash
git clone <url-do-repositório>
cd analisador-imovel
```

### 2. Instalar dependências
```bash
pip install streamlit anthropic python-dotenv
```

### 3. Configurar a API key
```bash
cp .env.example .env
```
Abre o ficheiro `.env` e substitui `a_tua_chave_aqui` pela tua API key da Anthropic.
A chave pode ser obtida em [console.anthropic.com](https://console.anthropic.com).

### 4. Correr a app
```bash
streamlit run app.py
```

A app abre automaticamente em `http://localhost:8501`.

## Stack

- Python
- Streamlit
- Anthropic API (claude-haiku-4-5)
