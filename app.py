import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Painel Metanol - Vigilância e Resposta",
    page_icon="⚠️",
    layout="wide"
)

ARQUIVO_PADRAO = Path("data/casos_metanol_exemplo.csv")

MUNICIPIOS_COORD = {
    "Cuiabá": (-15.6014, -56.0979),
    "Várzea Grande": (-15.6467, -56.1325),
    "Itanhangá": (-12.2259, -56.6462),
    "Nova Brasilândia": (-14.9612, -54.9685),
    "Querência": (-12.6093, -52.1821),
    "Barra do Garças": (-15.8916, -52.2567),
    "Rondonópolis": (-16.4673, -54.6372),
    "Sinop": (-11.8604, -55.5091),
    "Tangará da Serra": (-14.6229, -57.4933),
    "Cáceres": (-16.0764, -57.6818),
    "Sorriso": (-12.5425, -55.7211),
    "Lucas do Rio Verde": (-13.0705, -55.9235),
}

CLASS_ORDER = ["Confirmado", "Em investigação", "Descartado"]

@st.cache_data
def carregar_dados(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(ARQUIVO_PADRAO)

    for col in ["data_notificacao", "data_evolucao"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "idade" in df.columns:
        df["idade"] = pd.to_numeric(df["idade"], errors="coerce")

    if "tempo_ate_atendimento_horas" in df.columns:
        df["tempo_ate_atendimento_horas"] = pd.to_numeric(df["tempo_ate_atendimento_horas"], errors="coerce")

    if "municipio_residencia" in df.columns:
        df["latitude"] = df["municipio_residencia"].map(lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[0])
        df["longitude"] = df["municipio_residencia"].map(lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[1])

    return df

def card(label, value, help_text=None):
    st.metric(label=label, value=value, help=help_text)

def pct(num, den):
    if den == 0:
        return 0
    return round((num / den) * 100, 1)

def filtrar(df):
    with st.sidebar:
        st.title("Filtros")
        st.caption("Painel operacional para vigilância, investigação de exposição e resposta assistencial.")

        uploaded_file = st.file_uploader("Carregar CSV atualizado", type=["csv"])

        classificacoes = sorted(df["classificacao"].dropna().unique()) if "classificacao" in df.columns else []
        regionais = sorted(df["regional_saude"].dropna().unique()) if "regional_saude" in df.columns else []
        municipios = sorted(df["municipio_residencia"].dropna().unique()) if "municipio_residencia" in df.columns else []

        sel_class = st.multiselect("Classificação", classificacoes, default=classificacoes)
        sel_reg = st.multiselect("Regional de saúde", regionais, default=regionais)
        sel_mun = st.multiselect("Município de residência", municipios, default=municipios)

        data_min = df["data_notificacao"].min() if "data_notificacao" in df.columns else None
        data_max = df["data_notificacao"].max() if "data_notificacao" in df.columns else None
        intervalo = None
        if pd.notna(data_min) and pd.notna(data_max):
            intervalo = st.date_input("Período de notificação", (data_min.date(), data_max.date()))

        st.divider()
        st.markdown("**Campos mínimos recomendados no CSV**")
        st.code(
            "id_caso, data_notificacao, semana_epidemiologica, municipio_residencia, "
            "regional_saude, sexo, idade, classificacao, evolucao, bebida_suspeita, "
            "lote_suspeito, antidoto_utilizado, investigacao_vigilancia",
            language="text"
        )

    dff = df.copy()

    if sel_class and "classificacao" in dff.columns:
        dff = dff[dff["classificacao"].isin(sel_class)]

    if sel_reg and "regional_saude" in dff.columns:
        dff = dff[dff["regional_saude"].isin(sel_reg)]

    if sel_mun and "municipio_residencia" in dff.columns:
        dff = dff[dff["municipio_residencia"].isin(sel_mun)]

    if intervalo and len(intervalo) == 2 and "data_notificacao" in dff.columns:
        ini = pd.to_datetime(intervalo[0])
        fim = pd.to_datetime(intervalo[1])
        dff = dff[(dff["data_notificacao"] >= ini) & (dff["data_notificacao"] <= fim)]

    return dff, uploaded_file

# Carrega primeiro o exemplo para criar filtros.
df_inicial = carregar_dados()
dff, uploaded = filtrar(df_inicial)
if uploaded is not None:
    df_inicial = carregar_dados(uploaded)
    dff, _ = filtrar(df_inicial)

st.title("Painel Metanol — Vigilância e Resposta")
st.caption("Modelo operacional para monitoramento de intoxicação por metanol, investigação de exposição e apoio à tomada de decisão.")

total = len(dff)
confirmados = int((dff["classificacao"] == "Confirmado").sum()) if "classificacao" in dff.columns else 0
descartados = int((dff["classificacao"] == "Descartado").sum()) if "classificacao" in dff.columns else 0
investigacao = int((dff["classificacao"] == "Em investigação").sum()) if "classificacao" in dff.columns else 0
obitos = int((dff["evolucao"] == "Óbito").sum()) if "evolucao" in dff.columns else 0
letalidade = pct(obitos, confirmados)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    card("Casos notificados", total)
with c2:
    card("Confirmados", confirmados)
with c3:
    card("Descartados", descartados)
with c4:
    card("Em investigação", investigacao)
with c5:
    card("Óbitos confirmados", obitos, f"Letalidade entre confirmados: {letalidade}%")

if investigacao > 0:
    st.warning(f"Há {investigacao} caso(s) em investigação. Priorizar encerramento, vínculo de exposição e rastreamento de lote/bebida.")
if obitos > 0:
    st.error(f"Foram registrados {obitos} óbito(s). Reforçar alerta assistencial, acesso a antídoto e investigação de exposição comum.")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "1. Situação geral",
    "2. Linha do tempo",
    "3. Distribuição territorial",
    "4. Exposição e lotes",
    "5. Assistência e antídoto",
    "6. Base nominal",
    "7. Fluxo operacional"
])

with tab1:
    st.subheader("Distribuição por classificação, evolução e perfil")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "classificacao" in dff.columns and not dff.empty:
            class_counts = dff["classificacao"].value_counts().reindex(CLASS_ORDER).dropna().reset_index()
            class_counts.columns = ["classificacao", "casos"]
            fig = px.bar(class_counts, x="classificacao", y="casos", text="casos", title="Casos por classificação")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "evolucao" in dff.columns and not dff.empty:
            evo = dff["evolucao"].fillna("Não informado").value_counts().reset_index()
            evo.columns = ["evolucao", "casos"]
            fig = px.pie(evo, names="evolucao", values="casos", title="Evolução")
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        if "sexo" in dff.columns and not dff.empty:
            sexo = dff["sexo"].fillna("Não informado").value_counts().reset_index()
            sexo.columns = ["sexo", "casos"]
            fig = px.bar(sexo, x="sexo", y="casos", text="casos", title="Casos por sexo")
            st.plotly_chart(fig, use_container_width=True)

    if "idade" in dff.columns and dff["idade"].notna().any():
        fig = px.histogram(dff, x="idade", nbins=10, title="Distribuição por idade")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Curva por data de notificação e semana epidemiológica")

    if "data_notificacao" in dff.columns and dff["data_notificacao"].notna().any():
        curva = (
            dff.dropna(subset=["data_notificacao"])
            .groupby(["data_notificacao", "classificacao"])
            .size()
            .reset_index(name="casos")
        )
        fig = px.line(curva, x="data_notificacao", y="casos", color="classificacao", markers=True, title="Notificações por data")
        st.plotly_chart(fig, use_container_width=True)

    if "semana_epidemiologica" in dff.columns:
        se = dff.groupby(["semana_epidemiologica", "classificacao"]).size().reset_index(name="casos")
        fig = px.bar(se, x="semana_epidemiologica", y="casos", color="classificacao", text="casos", title="Casos por semana epidemiológica")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Distribuição territorial")

    col1, col2 = st.columns([1, 1])

    with col1:
        if "regional_saude" in dff.columns:
            reg = dff["regional_saude"].fillna("Não informado").value_counts().reset_index()
            reg.columns = ["regional_saude", "casos"]
            fig = px.bar(reg, x="regional_saude", y="casos", text="casos", title="Casos por regional")
            fig.update_layout(xaxis_title="", yaxis_title="Casos")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "municipio_residencia" in dff.columns:
            mun = dff["municipio_residencia"].fillna("Não informado").value_counts().reset_index()
            mun.columns = ["municipio_residencia", "casos"]
            fig = px.bar(mun, x="municipio_residencia", y="casos", text="casos", title="Casos por município")
            fig.update_layout(xaxis_title="", yaxis_title="Casos")
            st.plotly_chart(fig, use_container_width=True)

    map_df = dff.dropna(subset=["latitude", "longitude"]) if {"latitude", "longitude"}.issubset(dff.columns) else pd.DataFrame()
    if not map_df.empty:
        mapa = map_df.groupby(["municipio_residencia", "latitude", "longitude", "classificacao"]).size().reset_index(name="casos")
        fig = px.scatter_mapbox(
            mapa,
            lat="latitude",
            lon="longitude",
            size="casos",
            color="classificacao",
            hover_name="municipio_residencia",
            hover_data={"casos": True, "latitude": False, "longitude": False},
            zoom=4.5,
            height=520,
            title="Mapa de casos por município"
        )
        fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":50,"l":0,"b":0})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Para exibir mapa, inclua coordenadas ou municípios cadastrados no dicionário MUNICIPIOS_COORD do app.py.")

with tab4:
    st.subheader("Investigação de exposição, bebidas/lotes e vínculos epidemiológicos")
    st.info("Metanol não tem transmissão pessoa a pessoa. O painel deve rastrear exposição comum: bebida/lote/local de aquisição/consumo e pessoas expostas ao mesmo produto.")

    col1, col2 = st.columns(2)

    with col1:
        if "bebida_suspeita" in dff.columns:
            bebida = dff["bebida_suspeita"].fillna("Não informado").value_counts().reset_index()
            bebida.columns = ["bebida_suspeita", "casos"]
            fig = px.bar(bebida, x="bebida_suspeita", y="casos", text="casos", title="Bebida suspeita")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "lote_suspeito" in dff.columns:
            lote = dff["lote_suspeito"].fillna("Não informado").value_counts().reset_index()
            lote.columns = ["lote_suspeito", "casos"]
            fig = px.bar(lote, x="lote_suspeito", y="casos", text="casos", title="Lote suspeito")
            st.plotly_chart(fig, use_container_width=True)

    campos = [c for c in ["id_caso", "municipio_residencia", "classificacao", "exposicao_principal", "bebida_suspeita", "lote_suspeito", "uso_concomitante_outras_substancias", "investigacao_vigilancia"] if c in dff.columns]
    st.dataframe(dff[campos], use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Assistência, antídoto e gravidade")

    col1, col2, col3 = st.columns(3)

    with col1:
        if "antidoto_indicado" in dff.columns:
            ant_ind = dff["antidoto_indicado"].fillna("Não informado").value_counts().reset_index()
            ant_ind.columns = ["antidoto_indicado", "casos"]
            fig = px.bar(ant_ind, x="antidoto_indicado", y="casos", text="casos", title="Antídoto indicado")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if "antidoto_utilizado" in dff.columns:
            ant = dff["antidoto_utilizado"].fillna("Não informado").value_counts().reset_index()
            ant.columns = ["antidoto_utilizado", "casos"]
            fig = px.bar(ant, x="antidoto_utilizado", y="casos", text="casos", title="Antídoto utilizado")
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        if "necessitou_uti" in dff.columns:
            uti = dff["necessitou_uti"].fillna("Não informado").value_counts().reset_index()
            uti.columns = ["necessitou_uti", "casos"]
            fig = px.bar(uti, x="necessitou_uti", y="casos", text="casos", title="Necessitou UTI")
            st.plotly_chart(fig, use_container_width=True)

    if "tempo_ate_atendimento_horas" in dff.columns and dff["tempo_ate_atendimento_horas"].notna().any():
        tempo_mediano = dff["tempo_ate_atendimento_horas"].median()
        st.metric("Tempo mediano até atendimento", f"{tempo_mediano:.1f} horas")
        fig = px.box(dff, x="classificacao", y="tempo_ate_atendimento_horas", points="all", title="Tempo até atendimento por classificação")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    **Uso operacional desta aba**
    
    - Identificar atraso entre exposição, início de sintomas, atendimento e antídoto.
    - Monitorar necessidade de UTI, suporte ventilatório/hemodiálise quando os campos forem adicionados.
    - Apoiar logística de antídoto, comunicação com CIATOx, SAF, regulação e unidades de referência.
    """)

with tab6:
    st.subheader("Base nominal anonimizada / base de trabalho")
    st.dataframe(dff, use_container_width=True, hide_index=True)

    csv = dff.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "Baixar base filtrada em CSV",
        data=csv,
        file_name="base_filtrada_painel_metanol.csv",
        mime="text/csv"
    )

with tab7:
    st.subheader("Fluxo operacional sugerido")

    st.markdown("""
    ### 1. Detecção e notificação
    - Unidade assistencial identifica quadro suspeito compatível com intoxicação por metanol.
    - Notificação imediata à vigilância municipal, CIEVS Estadual e rede assistencial definida.
    - Registro no sistema pactuado e abertura de investigação epidemiológica.

    ### 2. Investigação de exposição
    - Levantar bebida/produto consumido, local, data, lote, marca, origem e pessoas expostas ao mesmo produto.
    - Acionar vigilância sanitária para coleta, interdição cautelar e rastreabilidade quando indicado.
    - Consolidar cadeia de exposição: paciente → produto → lote/local → demais expostos.

    ### 3. Resposta assistencial
    - Acionar CIATOx para orientação clínica.
    - Garantir fluxo para antídoto, suporte intensivo e regulação conforme gravidade.
    - Monitorar tempo até atendimento, uso de antídoto, UTI e evolução.

    ### 4. Gestão e comunicação de risco
    - Atualizar situação dos casos e lotes suspeitos diariamente durante o evento.
    - Emitir alerta à rede assistencial e aos municípios com exposição provável.
    - Reforçar orientação pública: não consumir bebidas de origem/procedência duvidosa.
    """)

    st.divider()
    st.markdown("### Campos adicionais recomendados para versão 2")
    st.code(
        """
data_exposicao
data_inicio_sintomas
data_primeiro_atendimento
data_antidoto
local_consumo
local_compra
marca
fabricante
numero_lacre
amostra_coletada
resultado_laboratorial_metanol
ph
anion_gap
osmolar_gap
hemodialise
ventilacao_mecanica
ciatox_acionado
regulacao_acionada
vigilancia_sanitaria_acionada
mapa_estoque_antidoto
        """,
        language="text"
    )
