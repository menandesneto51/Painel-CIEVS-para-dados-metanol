@echo off
title Painel Metanol - Vigilancia e Resposta
cd /d "%~dp0"

echo ============================================================
echo   PAINEL METANOL - VIGILANCIA E RESPOSTA
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Instalando/atualizando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Abrindo painel em http://localhost:8501
streamlit run app.py

pause
