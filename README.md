# Painel CIEVS para Dados de Metanol

Painel operacional em **Streamlit** e versão estática em HTML para monitoramento de casos suspeitos, confirmados e descartados relacionados à intoxicação por metanol em Mato Grosso.

## Situação da base

A base desidentificada foi atualizada em **05/08/2026**, a partir da planilha institucional `Casos Metanol MT - 2025 - Casos Metanol -MT.xlsx`.

| Indicador | Total |
|---|---:|
| Casos notificados | 17 |
| Confirmados | 7 |
| Descartados | 9 |
| Em investigação | 1 |
| Óbitos entre confirmados | 4 |
| Óbito em caso descartado | 1 |

A última notificação registrada na planilha ocorreu em **12/07/2026**, no município de **Novo Santo Antônio**, permanecendo em investigação na data da atualização.

## Regras aplicadas na atualização

- nomes dos pacientes e números SINAN não são publicados;
- grafias municipais foram normalizadas, incluindo `Itanhangá` e `Novo Santo Antônio`;
- as regiões de saúde foram padronizadas conforme a organização territorial da SES-MT;
- campos ausentes foram mantidos como `Não informado`, sem inferir ausência do evento;
- a planilha-fonte não possui campo explícito de sexo; essa informação foi publicada como `Não informado`, sem inferência a partir do nome;
- o indicador de óbitos considera somente casos com `classificacao = Confirmado` e `evolucao = Óbito`;
- óbito ocorrido em caso descartado é apresentado separadamente e não compõe a letalidade por metanol;
- a versão estática (`index.html`) passou a carregar diretamente o mesmo CSV utilizado pelo Streamlit, evitando divergência entre as duas apresentações.

## Estrutura do projeto

```text
.
├── app.py
├── index.html
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── data/
│   ├── casos_metanol.csv
│   └── casos_metanol_exemplo.csv
└── rodar_painel_metanol.bat
```

## Como rodar localmente no Windows

```bat
rodar_painel_metanol.bat
```

Ou manualmente:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Publicação no Streamlit Community Cloud

- **Branch:** `main`
- **Main file path:** `app.py`

## Campos esperados no CSV

```text
id_caso
data_notificacao
semana_epidemiologica
municipio_residencia
municipio_atendimento
regional_saude
sexo
idade
classificacao
criterio_confirmacao
evolucao
data_evolucao
exposicao_principal
bebida_suspeita
lote_suspeito
uso_concomitante_outras_substancias
sintomas
cid_suspeito
antidoto_indicado
antidoto_utilizado
tempo_ate_atendimento_horas
necessitou_uti
investigacao_vigilancia
observacao
```

## Observação epidemiológica

Metanol **não possui transmissão pessoa a pessoa**. O monitoramento deve priorizar a investigação de **exposição comum**, especialmente bebida, marca, lote, local de aquisição/consumo e demais pessoas expostas ao mesmo produto.

A base nominal original deve permanecer em ambiente institucional restrito, observando as regras de proteção de dados pessoais e sensíveis.
