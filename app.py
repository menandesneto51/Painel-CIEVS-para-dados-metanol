from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Painel Metanol - CIEVS",
    page_icon="⚠️",
    layout="wide",
)

DATA_PATH = Path("data/casos_metanol.csv")

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
    "Município em investigação": (None, None),
}


@st.cache_data
def load_data(uploaded_file=None) -> pd.DataFrame:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_csv(DATA_PATH)

    for col in ["data_notificacao", "data_evolucao"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["idade", "semana_epidemiologica", "tempo_ate_atendimento_horas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["latitude"] = df["municipio_residencia"].map(lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[0])
    df["longitude"] = df["municipio_residencia"].map(lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[1])
    return df


def pct(num: int, den: int) -> float:
    return round((num / den) * 100, 1) if den else 0.0


def value_counts_chart(df: pd.DataFrame, col: str, title: str):
    if col not in df.columns or df.empty:
        st.info(f"Sem dados para {title.lower()}.")
        return
    base = df[col].fillna("Não informado").value_counts().reset_index()
    base.columns = [col, "casos"]
    fig = px.bar(base, x=col, y="casos", text="casos", title=title)
    fig.update_layout(xaxis_title="", yaxis_title="Casos")
    st.plotly_chart(fig, use_container_width=True)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.title("Filtros")
        uploaded = st.file_uploader("Carregar CSV atualizado", type=["csv"])
        if uploaded is not None:
            df = load_data(uploaded)

        classif = sorted(df["classificacao"].dropna().unique())
        regionais = sorted(df["regional_saude"].dropna().unique())
        municipios = sorted(df["municipio_residencia"].dropna().unique())

        sel_classif = st.multiselect("Classificação", classif, default=classif)
        sel_regionais = st.multiselect("Regional de saúde", regionais, default=regionais)
        sel_municipios = st.multiselect("Município de residência", municipios, default=municipios)

        data_min = df["data_notificacao"].min()
        data_max = df["data_notificacao"].max()
        periodo = st.date_input("Período de notificação", (data_min.date(), data_max.date()))

    out = df.copy()
    if sel_classif:
        out = out[out["classificacao"].isin(sel_classif)]
    if sel_regionais:
        out = out[out["regional_saude"].isin(sel_regionais)]
    if sel_municipios:
        out = out[out["municipio_residencia"].isin(sel_municipios)]
    if periodo and len(periodo) == 2:
        out = out[
            (out["data_notificacao"] >= pd.to_datetime(periodo[0]))
            & (out["data_notificacao"] <= pd.to_datetime(periodo[1]))
        ]
    return out


df = load_data()
dff = apply_filters(df)

st.title("Painel CIEVS — Dados de Metanol")
st.caption(
    "Monitoramento operacional de intoxicação por metanol, com foco em situação dos casos, "
    "exposição comum, lotes/bebidas suspeitas, assistência e evolução."
)

total = len(dff)
confirmados = int((dff["classificacao"] == "Confirmado").sum())
descartados = int((dff["classificacao"] == "Descartado").sum())
investigacao = int((dff["classificacao"] == "Em investigação").sum())
obitos = int((dff["evolucao"] == "Óbito").sum())
letalidade = pct(obitos, confirmados)

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Notificados", total)
c2.metric("Confirmados", confirmados)
c3.metric("Descartados", descartados)
c4.metric("Em investigação", investigacao)
c5.metric("Óbitos", obitos)
c6.metric("Letalidade", f"{letalidade}%")

if investigacao:
    st.warning(f"Há {investigacao} caso(s) em investigação. Priorizar vínculo de exposição, bebida/lote e encerramento.")
if obitos:
    st.error(f"Foram registrados {obitos} óbito(s). Reforçar alerta assistencial, antídoto, regulação e investigação da fonte.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Situação geral", "Tempo", "Território", "Exposição/assistência", "Base"]
)

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        value_counts_chart(dff, "classificacao", "Casos por classificação")
    with col2:
        value_counts_chart(dff, "evolucao", "Casos por evolução")
    with col3:
        value_counts_chart(dff, "sexo", "Casos por sexo")

    if "idade" in dff.columns and dff["idade"].notna().any():
        fig = px.histogram(dff, x="idade", nbins=12, title="Distribuição por idade")
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    curva = (
        dff.dropna(subset=["data_notificacao"])
        .groupby(["data_notificacao", "classificacao"])
        .size()
        .reset_index(name="casos")
    )
    fig = px.line(curva, x="data_notificacao", y="casos", color="classificacao", markers=True, title="Notificações por data")
    st.plotly_chart(fig, use_container_width=True)

    se = dff.groupby(["semana_epidemiologica", "classificacao"]).size().reset_index(name="casos")
    fig = px.bar(se, x="semana_epidemiologica", y="casos", color="classificacao", text="casos", title="Casos por semana epidemiológica")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        value_counts_chart(dff, "regional_saude", "Casos por regional de saúde")
    with col2:
        value_counts_chart(dff, "municipio_residencia", "Casos por município de residência")

    mapa = (
        dff.dropna(subset=["latitude", "longitude"])
        .groupby(["municipio_residencia", "latitude", "longitude", "classificacao"])
        .size()
        .reset_index(name="casos")
    )
    if not mapa.empty:
        fig = px.scatter_mapbox(
            mapa,
            lat="latitude",
            lon="longitude",
            size="casos",
            color="classificacao",
            hover_name="municipio_residencia",
            hover_data={"casos": True, "latitude": False, "longitude": False},
            zoom=4.4,
            height=520,
            title="Mapa de casos por município",
        )
        fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 45, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.info(
        "Metanol não tem transmissão pessoa a pessoa. A investigação deve focar exposição comum: "
        "bebida, lote, local de compra/consumo e outras pessoas expostas ao mesmo produto."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        value_counts_chart(dff, "bebida_suspeita", "Bebida suspeita")
    with col2:
        value_counts_chart(dff, "lote_suspeito", "Lote suspeito")
    with col3:
        value_counts_chart(dff, "antidoto_utilizado", "Antídoto utilizado")

    cols = [
        "id_caso", "data_notificacao", "municipio_residencia", "classificacao",
        "evolucao", "data_evolucao", "bebida_suspeita", "lote_suspeito",
        "antidoto_indicado", "antidoto_utilizado", "investigacao_vigilancia",
    ]
    st.dataframe(dff[[c for c in cols if c in dff.columns]], use_container_width=True, hide_index=True)

with tab5:
    st.dataframe(dff, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar base filtrada",
        dff.to_csv(index=False, encoding="utf-8-sig"),
        file_name="base_filtrada_metanol.csv",
        mime="text/csv",
    )
