import json
import os
import re

import anthropic
import streamlit as st
from dotenv import load_dotenv

# Carregar variável de ambiente a partir do ficheiro .env
load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Inicializar estado da sessão para a renda estimada antes de criar widgets
if "renda_estimada" not in st.session_state:
    st.session_state["renda_estimada"] = 0.0

st.set_page_config(
    page_title="Analisador de Investimento Imobiliário",
    page_icon="🏘️",
    layout="centered",
)
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {
        background-color: #f0f4f0;
    }

    /* Título principal */
    h1 {
        color: #1B4332;
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    /* Headers de secção */
    h2, h3 {
        color: #2D6A4F;
        font-weight: 700;
    }

    /* Botão primário */
    .stButton > button[kind="primary"] {
        background-color: #1B4332;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: background-color 0.2s;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #2D6A4F;
    }

    /* Botões secundários */
    .stButton > button {
        border-radius: 8px;
        border: 2px solid #1B4332;
        color: #1B4332;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #1B4332;
        color: white;
    }

    /* Cards de métricas */
    [data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(27, 67, 50, 0.1);
        border-left: 4px solid #1B4332;
    }

    /* Valor da métrica */
    [data-testid="stMetricValue"] {
        color: #1B4332;
        font-weight: 700;
    }

    /* Caixa de análise qualitativa */
    .stAlert {
        background-color: #d8f3dc;
        border-left: 4px solid #1B4332;
        border-radius: 8px;
        color: #1B4332;
    }

    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        border-radius: 8px;
        border: 1.5px solid #b7d7c2;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #1B4332;
        box-shadow: 0 0 0 2px rgba(27, 67, 50, 0.15);
    }

    /* Selectbox */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 1.5px solid #b7d7c2;
    }

    /* Separadores */
    hr {
        border-color: #b7d7c2;
    }

    /* Rodapé */
    .stCaption {
        color: #2D6A4F;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏘️ Analisador de Investimento Imobiliário")
st.write(
    "Preencha os dados do imóvel e obtenha uma avaliação de rentabilidade e uma análise qualitativa."
)

# --- Funções auxiliares ---

def parse_float(value):
    """Interpreta valores numéricos opcionais em texto."""
    if not value or value.strip() == "":
        return None
    normalized = value.replace("€", "").replace(" ", "").replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return None


def extract_first_number(text):
    """Extrai o primeiro número de uma string."""
    match = re.search(r"([-+]?[0-9]*\.?[0-9]+)", text.replace("€", ""))
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def format_euro(valor):
    """Formata número em euros no padrão português: milhares com ponto e decimais com vírgula."""
    try:
        v = float(valor)
    except Exception:
        return "0,00 €"
    sign = "-" if v < 0 else ""
    av = abs(v)
    s = f"{av:,.2f}"
    # Converte formato en_US (123,456.78) para pt-PT (123.456,78)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{sign}{s} €"


# --- Funções de chamada à API ---

def estimate_renda_mensal(concelho, area, preco, estado):
    """Estima a renda mensal com base nos dados do imóvel."""
    prompt = (
        "Estimativa de renda mensal para um imóvel residencial em Portugal. "
        f"Concelho: {concelho}. Área: {area:.2f} m². Preço de compra: {preco:.2f} €. "
        f"Estado de conservação: {estado}. "
        "Responde apenas com um valor numérico em euros, sem outras palavras."
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_first_number(response.content[0].text)


def estimate_optional_costs(concelho, preco, estado):
    """Estima despesas opcionais com base nos dados do imóvel."""
    prompt = (
        "Estimativa de despesas para um imóvel residencial em Portugal. "
        f"Concelho: {concelho}. Preço de compra: {preco:.2f} €. "
        f"Estado de conservação: {estado}. "
        "Responde apenas com JSON válido com as chaves: "
        "condominio_mensal, imi_anual, manutencao_anual. "
        "Os valores devem estar em euros."
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_text = re.search(r"\{.*\}", text, re.DOTALL)
        if json_text:
            try:
                return json.loads(json_text.group(0))
            except json.JSONDecodeError:
                pass
    return None


def generate_analysis(concelho, preco, area, estado, renda_mensal, condominio, imi, manutencao):
    """Gera análise qualitativa do investimento imobiliário."""
    preco_m2 = preco / area
    renda_anual = renda_mensal * 12
    despesas_anuais = condominio * 12 + imi + manutencao
    yield_bruta = renda_anual / preco * 100
    yield_liquida = (renda_anual - despesas_anuais) / preco * 100

    prompt = f"""És um analista imobiliário experiente especializado no mercado português.
Avalia este investimento e devolve um texto em português europeu com estas 5 secções claramente separadas:

1) PREÇO POR M²
Avalia o preço por m² face à média estimada para o concelho. Indica se está acima, abaixo ou dentro da média.

2) ANÁLISE DA RENDA
Avalia se a renda mensal proposta de {renda_mensal:.2f} € é adequada face ao preço do imóvel ({preco:.2f} €), 
à área ({area:.2f} m²) e ao concelho. 
Indica claramente:
- Se a renda está abaixo, acima ou dentro do valor de mercado
- Qual o valor de renda mínimo para que o investimento seja atrativo (yield líquida acima de 4%)
- Qual o valor de renda que considerarias ideal para este imóvel neste concelho

3) PERFIL DE RISCO
Classifica o risco do investimento (Baixo / Médio / Alto) e justifica em 2-3 linhas.

4) RED FLAGS
Lista 3 a 5 perguntas críticas ou alertas que o investidor deve considerar antes de comprar.

5) VEREDICTO FINAL
Termina com exatamente uma destas frases seguida de uma justificação de 1 linha:
'Vale a pena investigar mais' ou 'Red flags significativos'

Dados do imóvel:
Concelho: {concelho}
Preço de compra: {preco:.2f} €
Área: {area:.2f} m²
Preço/m²: {preco_m2:.2f} €
Estado: {estado}
Renda mensal proposta: {renda_mensal:.2f} €
Condomínio mensal: {condominio:.2f} €
IMI anual: {imi:.2f} €
Manutenção anual: {manutencao:.2f} €
Yield bruta anual: {yield_bruta:.2f}%
Yield líquida anual: {yield_liquida:.2f}%
Despesas anuais totais: {despesas_anuais:.2f} €

Sê direto, específico e útil. Usa os dados fornecidos para fundamentar cada ponto."""

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()



# --- Interface ---

st.header("Dados do imóvel")

col1, col2 = st.columns(2)
with col1:
    preco_compra = st.number_input("Preço de compra (€)", min_value=1.0, step=1000.0, format="%.2f")
with col2:
    area = st.number_input("Área do imóvel (m²)", min_value=1.0, step=1.0, format="%.2f")

concelhos = [
    "Abrantes", "Aguiar da Beira", "Alandroal", "Albergaria-a-Velha", "Albufeira",
    "Alcácer do Sal", "Alcanena", "Alcobaça", "Alcochete", "Alcoutim", "Alenquer",
    "Alfândega da Fé", "Alijó", "Aljezur", "Aljustrel", "Almada", "Almeida",
    "Almeirim", "Almodôvar", "Alpiarça", "Alter do Chão", "Alvaiázere", "Alvito",
    "Amadora", "Amarante", "Amares", "Anadia", "Ansião", "Arcos de Valdevez",
    "Arganil", "Armamar", "Arouca", "Arraiolos", "Arronches", "Arruda dos Vinhos",
    "Aveiro", "Avis", "Azambuja", "Baião", "Barcelos", "Barrancos", "Barreiro",
    "Batalha", "Beja", "Belmonte", "Benavente", "Bombarral", "Borba", "Boticas",
    "Braga", "Bragança", "Cabeceiras de Basto", "Cadaval", "Caldas da Rainha",
    "Caminha", "Campo Maior", "Cantanhede", "Carrazeda de Ansiães", "Carregal do Sal",
    "Cartaxo", "Cascais", "Castelo Branco", "Castelo de Paiva", "Castelo de Vide",
    "Castro Daire", "Castro Marim", "Castro Verde", "Celorico da Beira",
    "Celorico de Basto", "Chamusca", "Chaves", "Cinfães", "Coimbra",
    "Condeixa-a-Nova", "Constância", "Coruche", "Covilhã", "Crato", "Cuba",
    "Elvas", "Entroncamento", "Espinho", "Esposende", "Estarreja", "Estremoz",
    "Évora", "Fafe", "Faro", "Felgueiras", "Ferreira do Alentejo",
    "Ferreira do Zêzere", "Figueira da Foz", "Figueira de Castelo Rodrigo",
    "Figueiró dos Vinhos", "Fornos de Algodres", "Freixo de Espada à Cinta",
    "Fronteira", "Fundão", "Gavião", "Góis", "Golegã", "Gondomar", "Gouveia",
    "Grândola", "Guarda", "Guimarães", "Idanha-a-Nova", "Ílhavo", "Lagoa",
    "Lagos", "Lamego", "Leiria", "Lisboa", "Loulé", "Loures", "Lourinhã",
    "Lousã", "Lousada", "Mação", "Macedo de Cavaleiros", "Mafra", "Maia",
    "Manteigas", "Marco de Canaveses", "Marinha Grande", "Marvão", "Matosinhos",
    "Mealhada", "Meda", "Melgaço", "Mesão Frio", "Mira", "Miranda do Corvo",
    "Miranda do Douro", "Mirandela", "Mogadouro", "Moimenta da Beira", "Moita",
    "Monção", "Monchique", "Mondim de Basto", "Monforte", "Montalegre",
    "Montemor-o-Novo", "Montemor-o-Velho", "Montijo", "Mora", "Mortágua",
    "Moura", "Mourão", "Murça", "Murtosa", "Nazaré", "Nelas", "Nisa",
    "Óbidos", "Odemira", "Odivelas", "Oeiras", "Oleiros", "Olhão",
    "Oliveira de Azeméis", "Oliveira de Frades", "Oliveira do Bairro",
    "Oliveira do Hospital", "Ourém", "Ourique", "Ovar", "Paços de Ferreira",
    "Palmela", "Pampilhosa da Serra", "Paredes", "Paredes de Coura",
    "Pedrogão Grande", "Penacova", "Penafiel", "Penalva do Castelo",
    "Penamacor", "Penedono", "Penela", "Peniche", "Peso da Régua", "Pinhel",
    "Pombal", "Ponte da Barca", "Ponte de Lima", "Ponte de Sor", "Portalegre",
    "Portel", "Portimão", "Porto", "Porto de Mós", "Póvoa de Lanhoso",
    "Póvoa de Varzim", "Proença-a-Nova", "Redondo", "Reguengos de Monsaraz",
    "Resende", "Ribeira de Pena", "Rio Maior", "Sabrosa", "Sabugal",
    "Salvaterra de Magos", "Santa Comba Dão", "Santa Maria da Feira",
    "Santa Marta de Penaguião", "Santarém", "Santiago do Cacém", "Santo Tirso",
    "São Brás de Alportel", "São João da Madeira", "São João da Pesqueira",
    "São Pedro do Sul", "Sardoal", "Sátão", "Seia", "Seixal", "Sernancelhe",
    "Serpa", "Sertã", "Sesimbra", "Setúbal", "Sever do Vouga", "Silves",
    "Sines", "Sintra", "Sobral de Monte Agraço", "Soure", "Sousel", "Tábua",
    "Tabuaço", "Tarouca", "Tavira", "Terras de Bouro", "Tomar", "Tondela",
    "Torre de Moncorvo", "Torres Novas", "Torres Vedras", "Trancoso", "Trofa",
    "Vagos", "Vale de Cambra", "Valença", "Valongo", "Valpaços",
    "Vendas Novas", "Viana do Alentejo", "Viana do Castelo", "Vidigueira",
    "Vieira do Minho", "Vila de Rei", "Vila do Bispo", "Vila do Conde",
    "Vila Flor", "Vila Franca de Xira", "Vila Nova da Barquinha",
    "Vila Nova de Cerveira", "Vila Nova de Famalicão", "Vila Nova de Foz Côa",
    "Vila Nova de Gaia", "Vila Nova de Paiva", "Vila Nova de Poiares",
    "Vila Pouca de Aguiar", "Vila Real", "Vila Real de Santo António",
    "Vila Verde", "Vila Viçosa", "Vimioso", "Vinhais", "Viseu", "Vouzela",
]

col1, col2 = st.columns(2)
with col1:
    concelho = st.selectbox("Concelho", concelhos, index=None, placeholder="Pesquisa ou seleciona um concelho...")
with col2:
    estado = st.selectbox(
        "Estado de conservação",
        ["Novo", "Bom estado", "Precisa de obras", "Ruínas"],
    )

st.markdown("---")

st.header("Renda e despesas")

col1, col2 = st.columns([3, 1])
with col1:
    renda_mensal = st.number_input(
        "Renda mensal esperada (€)",
        min_value=0.0,
        step=50.0,
        format="%.2f",
        value=st.session_state["renda_estimada"],
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    estimar_renda = st.button("Não sei, estima tu")

condominio_text = st.text_input("Condomínio mensal (€) (opcional)")
imi_text = st.text_input("IMI anual (€) (opcional)")
manutencao_text = st.text_input("Manutenção anual estimada (€) (opcional)")

if estimar_renda:
    if not concelho:
        st.warning("Seleciona um concelho para estimar a renda.")
    else:
        with st.spinner("A estimar renda mensal..."):
            resultado = estimate_renda_mensal(concelho, area, preco_compra, estado)
            if resultado is None:
                st.error("Não foi possível estimar a renda. Tente novamente mais tarde.")
            else:
                st.session_state["renda_estimada"] = float(resultado)
                st.rerun()

condominio = parse_float(condominio_text)
imi = parse_float(imi_text)
manutencao = parse_float(manutencao_text)

if st.button("Calcular e analisar", type="primary"):
    if preco_compra <= 0 or area <= 0 or renda_mensal <= 0 or not concelho:
        st.error("Preencha todos os campos obrigatórios e certifique-se de que a renda é maior que zero.")
    else:
        if condominio is None or imi is None or manutencao is None:
            with st.spinner("A estimar despesas opcionais..."):
                estimativas = estimate_optional_costs(concelho, preco_compra, estado)
            if estimativas is None:
                st.error("Não foi possível estimar as despesas opcionais. Preencha manualmente.")
                st.stop()
            else:
                condominio = condominio if condominio is not None else float(estimativas.get("condominio_mensal", 0.0))
                imi = imi if imi is not None else float(estimativas.get("imi_anual", 0.0))
                manutencao = manutencao if manutencao is not None else float(estimativas.get("manutencao_anual", 0.0))

        if condominio is None or imi is None or manutencao is None:
            st.error("Preencha os valores opcionais ou deixe o sistema estimar automaticamente.")
        else:
            renda_anual = renda_mensal * 12
            preco_m2 = preco_compra / area
            despesas_anuais = condominio * 12 + imi + manutencao
            yield_bruta = renda_anual / preco_compra * 100
            yield_liquida = (renda_anual - despesas_anuais) / preco_compra * 100
            fluxo_positivo = renda_anual - despesas_anuais
            payback = preco_compra / fluxo_positivo if fluxo_positivo > 0 else None

            st.markdown("---")
            st.subheader("Resultados quantitativos")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Preço por m²", format_euro(preco_m2))
            col2.metric("Yield bruta", f"{yield_bruta:.2f}%")
            col3.metric("Yield líquida", f"{yield_liquida:.2f}%")
            col4.metric("Payback (anos)", f"{payback:.1f}" if payback is not None else "Negativo")

            st.markdown("---")
            with st.spinner("A gerar análise qualitativa..."):
                analise = generate_analysis(
                    concelho, preco_compra, area, estado,
                    renda_mensal, condominio, imi, manutencao,
                )

            st.subheader("📋 Análise qualitativa")
            st.info(analise)

st.markdown("---")
st.caption("Analisador de Investimento Imobiliário • Dados meramente indicativos")