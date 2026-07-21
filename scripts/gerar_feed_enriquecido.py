#!/usr/bin/env python3
"""Gera o feed enriquecido do Pinterest a partir do feed XML da Yampi.

O feed da Yampi não inclui google_product_category, o que limita a
distribuição dos produtos no Pinterest (aviso 157 nos diagnósticos do
catálogo). Este script baixa o feed original e injeta a tag
<g:google_product_category> em cada <item>, sem alterar nenhum outro campo
(manipulação por texto, preservando o XML original byte a byte no restante).

O resultado em data/feed_pinterest.xml é servido via raw.githubusercontent.com
e conectado como fonte de dados principal do catálogo no Pinterest.
"""
import re
import urllib.request

FEED_URL = "https://s3.amazonaws.com/images.yampi.me/xml/3845b0c0-9b21-11ea-a366-b5824485fb4c.xml"
SAIDA = "data/feed_pinterest.xml"

MAP = [
    ("Poltronas", "Furniture &gt; Chairs &gt; Arm Chairs, Recliners &amp; Sleeper Chairs"),
    ("Poltrona e Puff", "Furniture &gt; Chairs &gt; Arm Chairs, Recliners &amp; Sleeper Chairs"),
    ("Sofás Retráteis", "Furniture &gt; Sofas"),
    ("Sofás Cama", "Furniture &gt; Futons"),
    ("Sofás", "Furniture &gt; Sofas"),
    ("Cadeiras Office", "Furniture &gt; Office Furniture &gt; Office Chairs"),
    ("Cadeiras", "Furniture &gt; Chairs &gt; Kitchen &amp; Dining Room Chairs"),
    ("Puffs", "Furniture &gt; Ottomans"),
    ("Bancos", "Furniture &gt; Benches"),
    ("Banquetas", "Furniture &gt; Chairs &gt; Table &amp; Bar Stools"),
    ("Mesas de Jantar", "Furniture &gt; Tables &gt; Kitchen &amp; Dining Room Tables"),
    ("Mesas de Centro", "Furniture &gt; Tables &gt; Accent Tables &gt; Coffee Tables"),
    ("Mesas Laterais", "Furniture &gt; Tables &gt; Accent Tables &gt; End Tables"),
    ("Chaises", "Furniture &gt; Chairs &gt; Chaises"),
    ("Aparadores e Buffets", "Furniture &gt; Cabinets &amp; Storage &gt; Buffets &amp; Sideboards"),
    ("Camas", "Furniture &gt; Beds &amp; Accessories &gt; Beds &amp; Bed Frames"),
    ("Ombrelones", "Home &amp; Garden &gt; Lawn &amp; Garden &gt; Outdoor Living &gt; Outdoor Umbrellas &amp; Sunshades"),
    ("Iluminação", "Home &amp; Garden &gt; Lighting"),
    ("Esculturas", "Home &amp; Garden &gt; Decor &gt; Sculptures &amp; Statues"),
    ("Miniaturas", "Home &amp; Garden &gt; Decor &gt; Figurines"),
    ("Cabideiros", "Furniture &gt; Entryway Furniture &gt; Coat &amp; Hat Racks"),
]

TITLE_KW = [
    (r"poltrona", "Furniture &gt; Chairs &gt; Arm Chairs, Recliners &amp; Sleeper Chairs"),
    (r"sof[áa].*cama", "Furniture &gt; Futons"),
    (r"sof[áa]", "Furniture &gt; Sofas"),
    (r"cadeira", "Furniture &gt; Chairs &gt; Kitchen &amp; Dining Room Chairs"),
    (r"banqueta", "Furniture &gt; Chairs &gt; Table &amp; Bar Stools"),
    (r"banco", "Furniture &gt; Benches"),
    (r"puff", "Furniture &gt; Ottomans"),
    (r"mesa de centro", "Furniture &gt; Tables &gt; Accent Tables &gt; Coffee Tables"),
    (r"mesa lateral", "Furniture &gt; Tables &gt; Accent Tables &gt; End Tables"),
    (r"mesa", "Furniture &gt; Tables"),
    (r"chaise", "Furniture &gt; Chairs &gt; Chaises"),
    (r"lumin[áa]ria|abajur|pendente", "Home &amp; Garden &gt; Lighting"),
    (r"escultura", "Home &amp; Garden &gt; Decor &gt; Sculptures &amp; Statues"),
    (r"ombrelone", "Home &amp; Garden &gt; Lawn &amp; Garden &gt; Outdoor Living &gt; Outdoor Umbrellas &amp; Sunshades"),
    (r"cama", "Furniture &gt; Beds &amp; Accessories &gt; Beds &amp; Bed Frames"),
    (r"aparador|buffet", "Furniture &gt; Cabinets &amp; Storage &gt; Buffets &amp; Sideboards"),
]

RE_PRODUCT_TYPE = re.compile(r"<g:product_type>(.*?)</g:product_type>", re.S)
RE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def classificar(item_xml: str) -> str:
    m = RE_PRODUCT_TYPE.search(item_xml)
    product_type = m.group(1) if m else ""
    for chave, categoria in MAP:
        # o product_type no XML vem com entidades (&gt;), comparar sem elas
        if chave.lower() in product_type.replace("&gt;", ">").lower():
            return categoria
    m = RE_TITLE.search(item_xml)
    titulo = (m.group(1) if m else "").lower()
    for padrao, categoria in TITLE_KW:
        if re.search(padrao, titulo):
            return categoria
    return "Furniture"


def injetar(m: re.Match) -> str:
    item = m.group(0)
    if "<g:google_product_category>" in item:
        return item
    categoria = classificar(item)
    return item.replace(
        "</item>",
        f"<g:google_product_category>{categoria}</g:google_product_category></item>",
    )


def main() -> None:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        original = resp.read().decode("utf-8")

    itens = original.count("<item>")
    if itens < 1000:
        raise SystemExit(f"Feed suspeito: só {itens} itens — abortando sem sobrescrever.")

    enriquecido, n = re.subn(r"<item>.*?</item>", injetar, original, flags=re.S)
    if n != itens:
        raise SystemExit(f"Inconsistência: {itens} itens no feed, {n} processados.")

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(enriquecido)
    print(f"{n} itens enriquecidos em {SAIDA}")


if __name__ == "__main__":
    main()
