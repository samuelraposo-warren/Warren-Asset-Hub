# -*- coding: utf-8 -*-
"""Importa os pontos de rede a partir de um arquivo .drawio (draw.io).

Lê os rótulos do diagrama no padrão "R02 PPN 320" (rack, patch panel,
número do ponto), cria as tabelas do módulo se necessário e popula
Rack → PatchPanel → NetworkPoint de forma idempotente.

Uso:
    python importar_rede.py                 # procura um .drawio na pasta do projeto
    python importar_rede.py "caminho.drawio"

Comportamento:
  - de-duplica pontos repetidos (mesmo rack+painel+número);
  - registros que não batem com o padrão vão para 'rede_nao_reconhecidos.txt'
    (nada é descartado silenciosamente);
  - rodar de novo não duplica: pontos já existentes são mantidos.
"""
import glob
import html
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
REVIEW_FILE = os.path.join(BASE, "rede_nao_reconhecidos.txt")

# Rótulo esperado, já "limpo": rack (R02), painel (PPx), número.
_LABEL_RE = re.compile(r"^(R0?\d+)\s+(PP[A-Z])\s+(\d+)$", re.I)


def _clean(value):
    """Remove tags/entidades HTML do value do mxCell e normaliza espaços."""
    v = html.unescape(value)
    v = re.sub(r"<[^>]+>", " ", v)   # <font>, <br>, etc.
    v = html.unescape(v)
    v = re.sub(r"\s+", " ", v).strip()
    # Normaliza "R 02" -> "R02" (variação com espaço depois do R).
    v = re.sub(r"\bR\s+(?=\d)", "R", v)
    return v


def _find_drawio():
    files = sorted(glob.glob(os.path.join(BASE, "*.drawio")), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def parse_points(path):
    """Retorna (pontos_unicos, nao_reconhecidos).

    pontos_unicos: lista de (rack, painel, numero) sem duplicatas, na ordem
    de primeira aparição. nao_reconhecidos: lista de rótulos com texto que
    não bateram com o padrão.
    """
    xml = open(path, encoding="utf-8").read()
    values = re.findall(r'value="([^"]*)"', xml)

    seen = set()
    points = []
    unmatched = []
    for raw in values:
        c = _clean(raw)
        if not c:
            continue
        m = _LABEL_RE.match(c)
        if m:
            key = (m.group(1).upper(), m.group(2).upper(), int(m.group(3)))
            if key not in seen:
                seen.add(key)
                points.append(key)
        else:
            unmatched.append(c)
    return points, unmatched


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else _find_drawio()
    if not path or not os.path.exists(path):
        print("ERRO: arquivo .drawio não encontrado. Coloque-o na pasta do "
              "projeto ou passe o caminho como argumento.")
        sys.exit(1)

    print(f"Lendo: {os.path.basename(path)}")
    points, unmatched = parse_points(path)
    print(f"Pontos reconhecidos (únicos): {len(points)}")
    print(f"Rótulos não reconhecidos: {len(unmatched)}")

    # Salva os não reconhecidos para revisão manual.
    if unmatched:
        with open(REVIEW_FILE, "w", encoding="utf-8") as f:
            f.write("Rótulos do diagrama que NÃO batem com o padrão 'R0x PPx num'.\n")
            f.write("Revise manualmente (ex.: pontos sem painel, TVs, títulos).\n\n")
            for u in sorted(set(unmatched)):
                f.write(u + "\n")
        print(f"→ Lista salva em: {os.path.basename(REVIEW_FILE)}")

    # --- Grava no banco via ORM (cria tabelas se faltarem) ---
    from app import create_app
    from app.extensions import db
    from app.models.enums import PortStatus
    from app.models.network import NetworkPoint, PatchPanel, Rack

    app = create_app()
    with app.app_context():
        db.create_all()  # cria net_racks / net_patch_panels / net_areas / net_points

        racks = {}
        panels = {}
        created = existing = 0

        for rack_code, panel_code, number in points:
            rack = racks.get(rack_code)
            if rack is None:
                rack = Rack.query.filter_by(code=rack_code).first()
                if rack is None:
                    rack = Rack(code=rack_code, name=f"Sala técnica {rack_code}")
                    db.session.add(rack)
                    db.session.flush()
                racks[rack_code] = rack

            pkey = (rack_code, panel_code)
            panel = panels.get(pkey)
            if panel is None:
                panel = PatchPanel.query.filter_by(rack_id=rack.id, code=panel_code).first()
                if panel is None:
                    panel = PatchPanel(code=panel_code, rack_id=rack.id)
                    db.session.add(panel)
                    db.session.flush()
                panels[pkey] = panel

            point = NetworkPoint.query.filter_by(
                patch_panel_id=panel.id, number=number
            ).first()
            if point is None:
                db.session.add(NetworkPoint(
                    patch_panel_id=panel.id,
                    number=number,
                    label=f"{rack_code} {panel_code} {number}",
                    status=PortStatus.FREE,
                ))
                created += 1
            else:
                existing += 1

        db.session.commit()

        print("\n--- Resultado ---")
        print(f"Racks:   {Rack.query.count()}")
        print(f"Painéis: {PatchPanel.query.count()}")
        print(f"Pontos:  {NetworkPoint.query.count()}  (novos: {created}, já existiam: {existing})")
        print("Importação concluída.")


if __name__ == "__main__":
    main()
