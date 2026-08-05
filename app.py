from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Painel Metanol — CIEVS-MT",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARQUIVO_PADRAO = Path("data/casos_metanol.csv")
DATA_ATUALIZACAO = "05/08/2026"

MUNICIPIOS_COORD = {
    "Cuiabá": (-15.6014, -56.0979),
    "Várzea Grande": (-15.6467, -56.1325),
    "Itanhangá": (-12.2312, -56.6395),
    "Nova Brasilândia": (-14.9612, -54.9685),
    "Querência": (-12.6093, -52.1821),
    "Barra do Garças": (-15.8916, -52.2567),
    "Sorriso": (-12.5425, -55.7211),
    "Água Boa": (-14.0491, -52.1600),
    "Nova Mutum": (-13.8370, -56.0743),
    "Peixoto de Azevedo": (-10.2262, -54.9794),
    "Juína": (-11.3781, -58.7481),
    "Novo Santo Antônio": (-12.2900, -50.9688),
    "Goiânia": (-16.6869, -49.2648),
}

CLASS_ORDER = ["Confirmado", "Em investigação", "Descartado"]
CLASS_COLORS = {
    "Confirmado": "#c0392b",
    "Em investigação": "#d4a017",
    "Descartado": "#1e8449",
}

st.markdown(
    """
<style>
:root {
  --ses-azul: #1b3281;
  --ses-azul-escuro: #10245f;
  --cievs-laranja: #ed6b1a;
  --fundo: #f7f8fb;
  --linha: #dfe2ed;
}
.stApp { background: var(--fundo); }
div[data-testid="stMainBlockContainer"] { max-width: 1500px; padding-top: 1.2rem; }
h1, h2, h3 { color: var(--ses-azul-escuro); }
div[data-testid="stMetric"] {
  background: #fff;
  border: 1px solid var(--linha);
  border-top: 4px solid var(--ses-azul);
  border-radius: 4px;
  padding: .7rem .8rem;
}
.cabecalho-institucional {
  background: var(--ses-azul-escuro);
  color: white;
  border-bottom: 4px solid var(--cievs-laranja);
  padding: .75rem 1rem;
  margin: -1rem -1rem 1rem;
  font-weight: 700;
  letter-spacing: .04em;
}
.nota-fonte {
  color: #5b6577;
  font-size: .82rem;
}
.alerta-metodo {
  background: #fff;
  border: 1px solid var(--linha);
  border-left: 4px solid var(--cievs-laranja);
  padding: .75rem .9rem;
  margin-bottom: .8rem;
}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def carregar_dados(uploaded_file=None) -> pd.DataFrame:
    fonte = uploaded_file if uploaded_file is not None else ARQUIVO_PADRAO
    df = pd.read_csv(fonte)

    for col in ("data_notificacao", "data_evolucao"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ("idade", "tempo_ate_atendimento_horas", "semana_epidemiologica"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "municipio_residencia" in df.columns:
        df["latitude"] = df["municipio_residencia"].map(
            lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[0]
        )
        df["longitude"] = df["municipio_residencia"].map(
            lambda x: MUNICIPIOS_COORD.get(str(x), (None, None))[1]
        )

    return df


def pct(num: int, den: int) -> float:
    return round((num / den) * 100, 1) if den else 0.0


def filtrar(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown(
            '<div class="cabecalho-institucional">GOVERNO DE MATO GROSSO<br>'
            '<span style="font-weight:400">Secretaria de Estado de Saúde · CIEVS-MT</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("### Painel Metanol")
        st.caption("Vigilância, investigação de exposição e resposta assistencial.")

        uploaded_file = st.file_uploader(
            "Carregar base normalizada (CSV)",
            type=["csv"],
            help="A carga temporária não altera a base publicada no GitHub.",
        )
        if uploaded_file is not None:
            df = carregar_dados(uploaded_file)

        classificacoes = (
            [c for c in CLASS_ORDER if c in set(df.get("classificacao", []))]
            if "classificacao" in df.columns else []
        )
        regionais = sorted(df["regional_saude"].dropna().astype(str).unique())
        municipios = sorted(df["municipio_residencia"].dropna().astype(str).unique())

        sel_class = st.multiselect(
            "Classificação", classificacoes, default=classificacoes
        )
        sel_reg = st.multiselect("Região de saúde", regionais, default=regionais)
        sel_mun = st.multiselect(
            "Município de residência", municipios, default=municipios
        )

        intervalo = None
        if "data_notificacao" in df.columns and df["data_notificacao"].notna().any():
            data_min = df["data_notificacao"].min().date()
            data_max = df["data_notificacao"].max().date()
            intervalo = st.date_input(
                "Período de notificação", (data_min, data_max)
            )

        st.divider()
        st.caption(f"Base publicada: {DATA_ATUALIZACAO}")
        st.caption("Registros desidentificados; nomes e números SINAN não são exibidos.")

    dff = df.copy()
    if sel_class:
        dff = dff[dff["classificacao"].isin(sel_class)]
    if sel_reg:
        dff = dff[dff["regional_saude"].isin(sel_reg)]
    if sel_mun:
        dff = dff[dff["municipio_residencia"].isin(sel_mun)]
    if intervalo and len(intervalo) == 2:
        ini, fim = pd.to_datetime(intervalo[0]), pd.to_datetime(intervalo[1])
        dff = dff[
            (dff["data_notificacao"] >= ini) & (dff["data_notificacao"] <= fim)
        ]
    return dff


df = carregar_dados()
dff = filtrar(df)

st.title("Painel Metanol — Vigilância e Resposta")
ultima_notificacao = (
    df["data_notificacao"].max().strftime("%d/%m/%Y")
    if "data_notificacao" in df.columns and df["data_notificacao"].notna().any()
    else "não informada"
)
st.caption(
    f"Base atualizada em {DATA_ATUALIZACAO} · última notificação: {ultima_notificacao} · "
    "dados desidentificados para uso epidemiológico e operacional."
)

with st.expander("Como ler e interpretar este painel", expanded=False):
    st.markdown(
        """
1. **Comece pelos indicadores gerais:** total notificado, confirmados, descartados,
   casos em investigação e óbitos entre casos confirmados.
2. **Use os filtros da lateral** para restringir a análise por período, município,
   região de saúde ou classificação.
3. **Leia a linha do tempo** para identificar concentração temporal e novos eventos.
4. **No mapa**, o ponto representa o município de residência; o atendimento pode
   ter ocorrido em outro município.
5. **Exposição e bebidas** apoiam a investigação de vínculo comum. Metanol não é
   transmitido entre pessoas.
6. **Campos “Não informado”** representam lacunas da planilha-fonte e não devem ser
   interpretados como ausência do evento.
        """
    )

total = len(dff)
confirmados = int((dff["classificacao"] == "Confirmado").sum())
descartados = int((dff["classificacao"] == "Descartado").sum())
investigacao = int((dff["classificacao"] == "Em investigação").sum())
obitos_confirmados = int(
    (
        (dff["classificacao"] == "Confirmado")
        & (dff["evolucao"] == "Óbito")
    ).sum()
)
obitos_outras_causas = int(
    dff["evolucao"].fillna("").str.contains("Óbito por outra causa", case=False).sum()
)
letalidade = pct(obitos_confirmados, confirmados)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Casos notificados", total)
c2.metric("Confirmados", confirmados)
c3.metric("Descartados", descartados)
c4.metric("Em investigação", investigacao)
c5.metric(
    "Óbitos entre confirmados",
    obitos_confirmados,
    help=f"Letalidade entre confirmados no recorte: {letalidade}%",
)

if investigacao:
    st.warning(
        f"Há {investigacao} caso(s) em investigação. Priorizar encerramento, "
        "vínculo de exposição e rastreamento da bebida/lote."
    )
if obitos_confirmados:
    st.error(
        f"Foram registrados {obitos_confirmados} óbito(s) entre casos confirmados "
        f"(letalidade: {letalidade}%)."
    )
if obitos_outras_causas:
    st.info(
        f"Há {obitos_outras_causas} óbito(s) em caso(s) descartado(s), não incluído(s) "
        "no indicador de óbitos por metanol."
    )

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "1. Situação geral",
        "2. Linha do tempo",
        "3. Distribuição territorial",
        "4. Exposição e bebidas",
        "5. Assistência e gravidade",
        "6. Base de casos",
        "7. Fluxo operacional",
    ]
)

with tab1:
    st.subheader("Classificação, evolução e perfil dos casos")
    col1, col2, col3 = st.columns(3)

    with col1:
        class_counts = (
            dff["classificacao"]
            .value_counts()
            .reindex(CLASS_ORDER, fill_value=0)
            .rename_axis("classificacao")
            .reset_index(name="casos")
        )
        fig = px.bar(
            class_counts,
            x="classificacao",
            y="casos",
            color="classificacao",
            color_discrete_map=CLASS_COLORS,
            text="casos",
            title="Casos por classificação",
        )
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        evo = (
            dff["evolucao"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("evolucao")
            .reset_index(name="casos")
        )
        fig = px.pie(evo, names="evolucao", values="casos", title="Evolução")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        sexo = (
            dff["sexo"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("sexo")
            .reset_index(name="casos")
        )
        fig = px.bar(sexo, x="sexo", y="casos", text="casos", title="Casos por sexo")
        fig.update_layout(xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)

    if dff["idade"].notna().any():
        fig = px.histogram(
            dff,
            x="idade",
            color="classificacao",
            color_discrete_map=CLASS_COLORS,
            nbins=10,
            title="Distribuição por idade",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Curva de notificações")
    if dff["data_notificacao"].notna().any():
        curva = (
            dff.dropna(subset=["data_notificacao"])
            .groupby(["data_notificacao", "classificacao"])
            .size()
            .reset_index(name="casos")
        )
        fig = px.line(
            curva,
            x="data_notificacao",
            y="casos",
            color="classificacao",
            color_discrete_map=CLASS_COLORS,
            markers=True,
            title="Notificações por data",
        )
        st.plotly_chart(fig, use_container_width=True)

    se = (
        dff.dropna(subset=["semana_epidemiologica"])
        .groupby(["semana_epidemiologica", "classificacao"])
        .size()
        .reset_index(name="casos")
    )
    if not se.empty:
        fig = px.bar(
            se,
            x="semana_epidemiologica",
            y="casos",
            color="classificacao",
            color_discrete_map=CLASS_COLORS,
            text="casos",
            title="Casos por semana epidemiológica",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Distribuição territorial")
    col1, col2 = st.columns(2)

    with col1:
        reg = (
            dff["regional_saude"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("regional_saude")
            .reset_index(name="casos")
        )
        fig = px.bar(
            reg,
            x="regional_saude",
            y="casos",
            text="casos",
            title="Casos por região de saúde",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        mun = (
            dff["municipio_residencia"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("municipio_residencia")
            .reset_index(name="casos")
        )
        fig = px.bar(
            mun,
            x="municipio_residencia",
            y="casos",
            text="casos",
            title="Casos por município de residência",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)

    map_df = dff.dropna(subset=["latitude", "longitude"])
    if not map_df.empty:
        mapa = (
            map_df.groupby(
                [
                    "municipio_residencia",
                    "latitude",
                    "longitude",
                    "classificacao",
                ]
            )
            .size()
            .reset_index(name="casos")
        )
        fig = px.scatter_mapbox(
            mapa,
            lat="latitude",
            lon="longitude",
            size="casos",
            color="classificacao",
            color_discrete_map=CLASS_COLORS,
            hover_name="municipio_residencia",
            hover_data={"casos": True, "latitude": False, "longitude": False},
            zoom=4.4,
            height=520,
            title="Mapa de casos por município de residência",
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Investigação de exposição comum")
    st.markdown(
        '<div class="alerta-metodo"><b>Interpretação:</b> a análise de bebidas e '
        "substâncias auxilia a identificar exposições comuns. Ausência de lote "
        "informado é uma lacuna de investigação, não evidência de inexistência.</div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        bebida = (
            dff["bebida_suspeita"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("bebida_suspeita")
            .reset_index(name="casos")
        )
        fig = px.bar(
            bebida,
            x="bebida_suspeita",
            y="casos",
            text="casos",
            title="Bebida suspeita",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        subst = (
            dff["uso_concomitante_outras_substancias"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("substancia")
            .reset_index(name="casos")
        )
        fig = px.bar(
            subst,
            x="substancia",
            y="casos",
            text="casos",
            title="Uso concomitante informado",
        )
        fig.update_layout(xaxis_title="", yaxis_title="Casos")
        st.plotly_chart(fig, use_container_width=True)

    campos = [
        "id_caso",
        "data_notificacao",
        "municipio_residencia",
        "classificacao",
        "bebida_suspeita",
        "lote_suspeito",
        "uso_concomitante_outras_substancias",
        "investigacao_vigilancia",
    ]
    st.dataframe(dff[campos], use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Assistência, gravidade e desfecho")
    col1, col2, col3 = st.columns(3)

    with col1:
        uti = (
            dff["necessitou_uti"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("necessitou_uti")
            .reset_index(name="casos")
        )
        fig = px.bar(uti, x="necessitou_uti", y="casos", text="casos", title="Necessidade de UTI")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        antidoto = (
            dff["antidoto_utilizado"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("antidoto_utilizado")
            .reset_index(name="casos")
        )
        fig = px.bar(
            antidoto,
            x="antidoto_utilizado",
            y="casos",
            text="casos",
            title="Antídoto utilizado",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        inv = (
            dff["investigacao_vigilancia"]
            .fillna("Não informado")
            .value_counts()
            .rename_axis("investigacao")
            .reset_index(name="casos")
        )
        fig = px.bar(
            inv,
            x="investigacao",
            y="casos",
            text="casos",
            title="Situação da investigação",
        )
        st.plotly_chart(fig, use_container_width=True)

    assist = [
        "id_caso",
        "municipio_residencia",
        "municipio_atendimento",
        "classificacao",
        "evolucao",
        "data_evolucao",
        "necessitou_uti",
        "antidoto_indicado",
        "antidoto_utilizado",
        "sintomas",
    ]
    st.dataframe(dff[assist], use_container_width=True, hide_index=True)

with tab6:
    st.subheader("Base de casos desidentificada")
    st.caption(
        "A base publicada não contém nome do paciente nem número SINAN. "
        "Utilize a planilha nominal apenas em ambiente institucional restrito."
    )
    st.dataframe(dff, use_container_width=True, hide_index=True, height=520)
    st.download_button(
        "Baixar recorte em CSV",
        data=dff.drop(columns=["latitude", "longitude"], errors="ignore").to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="casos_metanol_recorte.csv",
        mime="text/csv",
    )

with tab7:
    st.subheader("Fluxo operacional recomendado")
    st.markdown(
        """
1. **Notificar e comunicar imediatamente** o caso suspeito ao CIEVS.
2. **Avaliar clinicamente** sinais neurológicos, visuais, gastrointestinais,
   acidose metabólica e necessidade de suporte intensivo.
3. **Articular assistência e toxicologia**, incluindo avaliação para antídoto.
4. **Coletar amostras e preservar evidências**, conforme o fluxo laboratorial e pericial.
5. **Investigar a exposição comum:** bebida, marca, lote, local de aquisição/consumo
   e demais pessoas expostas.
6. **Atualizar a classificação e evolução** até o encerramento.
7. **Comunicar risco** com orientação para não consumir bebidas de procedência duvidosa.
        """
    )

st.markdown(
    '<p class="nota-fonte">Fonte: planilha institucional “Casos Metanol MT — 2025”, '
    f"recebida para atualização em {DATA_ATUALIZACAO}. Municípios e grafias foram "
    "normalizados; campos ausentes foram mantidos como “Não informado”.</p>",
    unsafe_allow_html=True,
)
