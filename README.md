# Painel CIEVS para Dados de Metanol

Painel operacional em **Streamlit** para monitoramento de casos suspeitos, confirmados, descartados e em investigação relacionados à intoxicação por metanol.

## Situação da base incluída

A base `data/casos_metanol.csv` está atualizada com o caso confirmado informado em 16/06/2026:

- paciente do sexo feminino;
- residente em Querência/MT;
- caso confirmado;
- notificação em 06/06/2026;
- evolução para óbito em 15/06/2026.

Resumo atual da base:

| Indicador | Total |
|---|---:|
| Casos notificados | 16 |
| Confirmados | 7 |
| Descartados | 8 |
| Em investigação | 1 |
| Óbitos | 4 |

## Estrutura do projeto

```text
.
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── casos_metanol.csv
│   └── casos_metanol_exemplo.csv
└── rodar_painel_metanol.bat
```

## Como rodar localmente no Windows

Abra o Prompt de Comando ou PowerShell dentro da pasta do projeto e execute:

```bat
rodar_painel_metanol.bat
```

Ou rode manualmente:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Como publicar no Streamlit Community Cloud

1. Acesse o Streamlit Community Cloud.
2. Escolha este repositório no GitHub.
3. Configure:
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Clique em **Deploy**.

## Campos mínimos esperados no CSV

O painel espera preferencialmente as seguintes colunas:

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

Metanol **não possui transmissão pessoa a pessoa**. O painel prioriza investigação de **exposição comum**, especialmente bebida suspeita, lote, local de aquisição/consumo e demais pessoas expostas ao mesmo produto.
