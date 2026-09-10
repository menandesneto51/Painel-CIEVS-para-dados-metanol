from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unicodedata
from datetime import date, datetime
from pathlib import Path

import gdown
from openpyxl import load_workbook

DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID", "13sLXlRgOJFPWWxuRY6bbz0m8OJVG4-Gy")
SHEET_NAME = os.getenv("SHEET_NAME", "Cadastro de Casos")
INDEX_PATH = Path(os.getenv("INDEX_PATH", "index.html"))


def norm(v):
    if v is None:
        return ""
    s = str(v).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s).lower()


def fmt_date(v):
    if v in (None, ""):
        return None
    if isinstance(v, datetime):
        return v.strftime("%d/%m/%Y")
    if isinstance(v, date):
        return v.strftime("%d/%m/%Y")
    return str(v).strip()


def find_header_row(ws):
    for r in range(1, min(ws.max_row, 20) + 1):
        vals = [norm(ws.cell(r, c).value) for c in range(1, min(ws.max_column, 30) + 1)]
        if "id do caso" in vals and "status do caso" in vals:
            return r
    raise RuntimeError("Cabeçalho da aba 'Cadastro de Casos' não encontrado.")


def build_header_map(ws, header_row):
    return {norm(ws.cell(header_row, c).value): c for c in range(1, ws.max_column + 1) if ws.cell(header_row, c).value}


def col(h, *names):
    for name in names:
        key = norm(name)
        if key in h:
            return h[key]
    return None


def get(ws, r, c):
    return ws.cell(r, c).value if c else None


def download_sheet(target: Path):
    url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}&export=download"
    result = gdown.download(url=url, output=str(target), quiet=False, fuzzy=True)
    if not result or not target.exists() or target.stat().st_size < 1000:
        raise RuntimeError("Não foi possível baixar a planilha do Google Drive. Verifique se o arquivo está acessível por link.")


def read_cases(xlsx_path: Path):
    wb = load_workbook(xlsx_path, data_only=True, read_only=True)
    if SHEET_NAME not in wb.sheetnames:
        raise RuntimeError(f"Aba obrigatória '{SHEET_NAME}' não encontrada. Abas disponíveis: {wb.sheetnames}")
    ws = wb[SHEET_NAME]
    hr = find_header_row(ws)
    h = build_header_map(ws, hr)

    c_id = col(h, "ID do caso")
    c_data = col(h, "Data da notificação")
    c_status = col(h, "Status do caso")
    c_res = col(h, "Município de residência")
    c_int = col(h, "Município de internação")
    c_sexo = col(h, "Sexo")
    c_idade = col(h, "Idade (anos)", "Idade")
    c_grav = col(h, "Gravidade")
    c_desc = col(h, "Descrição clínica/laboratorial")
    c_evol = col(h, "Evolução")
    c_hosp = col(h, "Necessitou hospitalização?")
    c_perm = col(h, "Permanece hospitalizado?")
    c_ant = col(h, "Recebeu antídoto?")
    c_obito = col(h, "Óbito?")
    c_tipo = col(h, "Tipo de óbito")
    c_data_obito = col(h, "Data do óbito")
    c_obs = col(h, "Observações")
    c_pronto = col(h, "Pronto para publicar?")

    required = {
        "ID do caso": c_id,
        "Data da notificação": c_data,
        "Status do caso": c_status,
        "Município de residência": c_res,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise RuntimeError("Colunas obrigatórias ausentes: " + ", ".join(missing))

    cases = []
    seen_ids = set()
    skipped = []

    for r in range(hr + 1, ws.max_row + 1):
        raw_id = get(ws, r, c_id)
        if raw_id in (None, ""):
            continue
        try:
            case_id = int(raw_id)
        except Exception:
            raise RuntimeError(f"ID inválido na linha {r}: {raw_id!r}")
        if case_id in seen_ids:
            raise RuntimeError(f"ID duplicado na planilha: {case_id}")
        seen_ids.add(case_id)

        pronto = str(get(ws, r, c_pronto) or "").strip().lower() if c_pronto else ""
        if pronto in {"não", "nao"}:
            skipped.append(case_id)
            continue

        idade = get(ws, r, c_idade)
        if isinstance(idade, float) and idade.is_integer():
            idade = int(idade)

        sexo = str(get(ws, r, c_sexo) or "Não informado").strip()
        perfil_idade = idade if idade not in (None, "") else "não informada"

        cases.append({
            "id": case_id,
            "d": fmt_date(get(ws, r, c_data)),
            "s": str(get(ws, r, c_status) or "Não informado").strip(),
            "r": str(get(ws, r, c_res) or "Não informado").strip(),
            "i": str(get(ws, r, c_int) or "Não informado").strip(),
            "x": sexo,
            "a": idade if idade not in (None, "") else "Não informado",
            "g": str(get(ws, r, c_grav) or "Não informado").strip(),
            "c": str(get(ws, r, c_desc) or "").strip(),
            "e": str(get(ws, r, c_evol) or "Não informado").strip(),
            "h": str(get(ws, r, c_hosp) or "Não informado").strip(),
            "p": str(get(ws, r, c_perm) or "Não informado").strip(),
            "t": str(get(ws, r, c_ant) or "Não informado").strip(),
            "o": str(get(ws, r, c_obito) or "Não informado").strip(),
            "to": str(get(ws, r, c_tipo) or "Não se aplica").strip(),
            "do": fmt_date(get(ws, r, c_data_obito)),
            "obs": str(get(ws, r, c_obs) or "").strip(),
        })

    cases.sort(key=lambda x: x["id"])
    if not cases:
        raise RuntimeError("Nenhum registro apto para publicação foi encontrado.")
    return cases, skipped


def update_html(cases):
    html = INDEX_PATH.read_text(encoding="utf-8")
    payload = json.dumps(cases, ensure_ascii=False, separators=(",", ":"))

    patterns = [
        (r"const C=\[.*?\];const Z=", f"const C={payload};const Z="),
        (r"const CASOS=\[.*?\];\s*const COORDS=", f"const CASOS={payload};\nconst COORDS="),
    ]
    replaced = False
    for pattern, repl in patterns:
        new_html, n = re.subn(pattern, repl, html, count=1, flags=re.S)
        if n == 1:
            html = new_html
            replaced = True
            break
    if not replaced:
        raise RuntimeError("Bloco de dados do painel não foi localizado no index.html.")

    today = datetime.now().astimezone().strftime("%d/%m/%Y")
    html = re.sub(
        r"Dados carregados da planilha atualizada em \d{2}/\d{2}/\d{4}\.",
        f"Dados carregados da planilha atualizada em {today}.",
        html,
        count=1,
    )

    INDEX_PATH.write_text(html, encoding="utf-8")


def main():
    tmp = Path(tempfile.gettempdir()) / "metanol_drive.xlsx"
    if tmp.exists():
        tmp.unlink()
    download_sheet(tmp)
    cases, skipped = read_cases(tmp)
    update_html(cases)
    print(f"Registros publicados: {len(cases)}")
    print("IDs publicados:", ", ".join(str(c["id"]) for c in cases))
    if skipped:
        print("IDs explicitamente não prontos e não publicados:", ", ".join(map(str, skipped)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise
