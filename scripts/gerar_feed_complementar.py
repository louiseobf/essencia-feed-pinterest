#!/usr/bin/env python3
"""Gera o feed complementar do Pinterest (google_product_category) a partir do feed XML da Yampi.

O feed principal da Yampi (conectado ao catálogo do Pinterest) não inclui o campo
google_product_category. Este script baixa o feed, classifica cada item pela
categoria interna (product_type) com fallback por palavras-chave do título e
escreve data/pinterest_complementar.csv no formato aceito pelo Pinterest como
fonte de dados complementar (colunas: id, google_product_category).
"""
import csv
import html
import re
import urllib.request
import xml.etree.ElementTree as ET

FEED_URL = "https://s3.amazonaws.com/images.yampi.me/xml/3845b0c0-9b21-11ea-a366-b5824485fb4c.xml"
SAIDA = "data/pinterest_complementar.csv"
NS = {"g": "http://base.google.com/ns/1.0"}

# Mapeamento categoria interna (product_type da Yampi) -> taxonomia do Google
MAP = [
    ("Poltronas", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    ("Poltrona e Puff", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    ("Sofás Retráteis", "Furniture > Sofas"),
    ("Sofás Cama", "Furniture > Futons"),
    ("Sofás", "Furniture > Sofas"),
    ("Cadeiras Office", "Furniture > Office Furniture > Office Chairs"),
    ("Cadeiras", "Furniture > Chairs > Kitchen & Dining Room Chairs"),
    ("Puffs", "Furniture > Ottomans"),
    ("Bancos", "Furniture > Benches"),
    ("Banquetas", "Furniture > Chairs > Table & Bar Stools"),
    ("Mesas de Jantar", "Furniture > Tables > Kitchen & Dining Room Tables"),
    ("Mesas de Centro", "Furniture > Tables > Accent Tables > Coffee Tables"),
    ("Mesas Laterais", "Furniture > Tables > Accent Tables > End Tables"),
    ("Chaises", "Furniture > Chairs > Chaises"),
    ("Aparadores e Buffets", "Furniture > Cabinets & Storage > Buffets & Sideboards"),
    ("Camas", "Furniture > Beds & Accessories > Beds & Bed Frames"),
    ("Ombrelones", "Home & Garden > Lawn & Garden > Outdoor Living > Outdoor Umbrellas & Sunshades"),
    ("Iluminação", "Home & Garden > Lighting"),
    ("Esculturas", "Home & Garden > Decor > Sculptures & Statues"),
    ("Miniaturas", "Home & Garden > Decor > Figurines"),
    ("Cabideiros", "Furniture > Entryway Furniture > Coat & Hat Racks"),
]

# Fallback por palavras-chave no título, para itens em categorias de designer etc.
TITLE_KW = [
    (r"poltrona", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    (r"sof[áa].*cama", "Furniture > Futons"),
    (r"sof[áa]", "Furniture > Sofas"),
    (r"cadeira", "Furniture > Chairs > Kitchen & Dining Room Chairs"),
    (r"banqueta", "Furniture > Chairs > Table & Bar Stools"),
    (r"banco", "Furniture > Benches"),
    (r"puff", "Furniture > Ottomans"),
    (r"mesa de centro", "Furniture > Tables > Accent Tables > Coffee Tables"),
    (r"mesa lateral", "Furniture > Tables > Accent Tables > End Tables"),
    (r"mesa", "Furniture > Tables"),
    (r"chaise", "Furniture > Chairs > Chaises"),
    (r"lumin[áa]ria|abajur|pendente", "Home & Garden > Lighting"),
    (r"escultura", "Home & Garden > Decor > Sculptures & Statues"),
    (r"ombrelone", "Home & Garden > Lawn & Garden > Outdoor Living > Outdoor Umbrellas & Sunshades"),
    (r"cama", "Furniture > Beds & Accessories > Beds & Bed Frames"),
    (r"aparador|buffet", "Furniture > Cabinets & Storage > Buffets & Sideboards"),
]


def classificar(product_type: str, titulo: str) -> str:
    for chave, categoria in MAP:
        if chave.lower() in product_type.lower():
            return categoria
    t = titulo.lower()
    for padrao, categoria in TITLE_KW:
        if re.search(padrao, t):
            return categoria
    return "Furniture"


def main() -> None:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        tree = ET.parse(resp)

    linhas = []
    for item in tree.getroot().findall(".//item"):
        pid = item.find("g:id", NS).text.strip()
        pt = item.find("g:product_type", NS)
        pt = html.unescape(pt.text.strip()) if pt is not None and pt.text else ""
        titulo = item.findtext("title") or ""
        linhas.append((pid, classificar(pt, titulo)))

    with open(SAIDA, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "google_product_category"])
        w.writerows(sorted(linhas))

    print(f"{len(linhas)} itens gravados em {SAIDA}")


if __name__ == "__main__":
    main()
