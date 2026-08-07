#!/usr/bin/env python3
"""Gera o feed enriquecido do Pinterest a partir do feed XML da Yampi.

O feed da Yampi não inclui google_product_category, o que limita a
distribuição dos produtos no Pinterest (aviso 157 nos diagnósticos do
catálogo). Este script baixa o feed original e:

1. injeta a tag <g:google_product_category> em cada <item>, usando o nível
   mais profundo aplicável da taxonomia oficial do Google (aviso 126 cobra
   categorias rasas que tenham subcategorias);
2. substitui image_link definitivamente quebrado (4xx) pela imagem OK de
   outra variação do mesmo produto (alguns SKUs antigos apontam para
   arquivos removidos do servidor da Yampi — erro 1202 no Pinterest).

Todos os caminhos de categoria são validados manualmente contra
https://www.google.com/basepages/producttype/taxonomy.en-US.txt
"""
import re
import urllib.request
from xml.sax.saxutils import escape

FEED_URL = "https://s3.amazonaws.com/images.yampi.me/xml/3845b0c0-9b21-11ea-a366-b5824485fb4c.xml"
SAIDA = "data/feed_pinterest.xml"

# Mapeamento categoria interna (product_type da Yampi) -> taxonomia do Google.
# Strings em texto puro; o escape XML acontece na injeção.
MAP = [
    ("Poltronas", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    ("Poltrona e Puff", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    ("Sofás Retráteis", "Furniture > Sofas"),
    ("Sofás Cama", "Furniture > Futons"),
    ("Sofás", "Furniture > Sofas"),
    ("Cadeiras Office", "Furniture > Office Furniture > Office Chairs"),
    ("Cadeiras", "Furniture > Chairs > Kitchen & Dining Room Chairs"),
    ("Puffs", "Furniture > Ottomans"),
    ("Bancos", "@banco"),  # refinado por título abaixo
    ("Banquetas", "Furniture > Chairs > Table & Bar Stools"),
    ("Mesas de Jantar", "Furniture > Tables > Kitchen & Dining Room Tables"),
    ("Mesas de Centro", "Furniture > Tables > Accent Tables > Coffee Tables"),
    ("Mesas Laterais", "Furniture > Tables > Accent Tables > End Tables"),
    ("Chaises", "Furniture > Chairs > Chaises"),
    ("Aparadores e Buffets", "Furniture > Cabinets & Storage > Buffets & Sideboards"),
    ("Camas", "Furniture > Beds & Accessories > Beds & Bed Frames"),
    ("Ombrelones", "Home & Garden > Lawn & Garden > Outdoor Living > Outdoor Umbrellas & Sunshades"),
    ("Iluminação", "@iluminacao"),  # refinado por título abaixo
    ("Esculturas", "Home & Garden > Decor > Artwork > Sculptures & Statues"),
    ("Miniaturas", "Home & Garden > Decor > Figurines"),
    ("Cabideiros", "Home & Garden > Decor > Coat & Hat Racks"),
]

# Fallback por palavras-chave no título (ordem importa).
TITLE_KW = [
    (r"miniatura", "Home & Garden > Decor > Figurines"),
    (r"p[ôo]ster", "Home & Garden > Decor > Artwork > Posters, Prints, & Visual Artwork"),
    (r"l[âa]mpada.*led", "Home & Garden > Lighting > Light Bulbs > LED Light Bulbs"),
    (r"l[âa]mpada", "Home & Garden > Lighting > Light Bulbs > Incandescent Light Bulbs"),
    (r"pendente|lustre|plafon", "Home & Garden > Lighting > Lighting Fixtures > Ceiling Light Fixtures"),
    (r"lumin[áa]ria|abajur", "Home & Garden > Lighting > Lamps"),
    (r"clock|rel[óo]gio|sun burst", "Home & Garden > Decor > Clocks > Wall Clocks"),
    (r"e-?book", "Media > Books > E-books"),
    (r"cave cat|arranhador", "Animals & Pet Supplies > Pet Supplies > Cat Supplies > Cat Furniture"),
    (r"poltrona", "Furniture > Chairs > Arm Chairs, Recliners & Sleeper Chairs"),
    (r"sof[áa].*cama", "Furniture > Futons"),
    (r"sof[áa]", "Furniture > Sofas"),
    (r"cadeira", "Furniture > Chairs > Kitchen & Dining Room Chairs"),
    (r"banqueta", "Furniture > Chairs > Table & Bar Stools"),
    (r"banco", "@banco"),
    (r"puff", "Furniture > Ottomans"),
    (r"escultura", "Home & Garden > Decor > Artwork > Sculptures & Statues"),
    (r"ombrelone", "Home & Garden > Lawn & Garden > Outdoor Living > Outdoor Umbrellas & Sunshades"),
    (r"base de mesa", "Furniture > Table Accessories > Table Legs"),
    (r"mesa.*jantar", "Furniture > Tables > Kitchen & Dining Room Tables"),
    (r"mesa.*centro", "Furniture > Tables > Accent Tables > Coffee Tables"),
    (r"mesa.*lateral", "Furniture > Tables > Accent Tables > End Tables"),
    (r"mesa", "Furniture > Tables"),
    (r"chaise", "Furniture > Chairs > Chaises"),
    (r"cama", "Furniture > Beds & Accessories > Beds & Bed Frames"),
    (r"aparador|buffet", "Furniture > Cabinets & Storage > Buffets & Sideboards"),
]

RE_PRODUCT_TYPE = re.compile(r"<g:product_type>(.*?)</g:product_type>", re.S)
RE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
RE_LINK = re.compile(r"<link>(.*?)</link>", re.S)
RE_IMAGE = re.compile(r"<g:image_link>(.*?)</g:image_link>", re.S)


def _refinar(marcador: str, titulo: str) -> str:
    """Resolve os marcadores @... para o nível mais profundo pela pista do título."""
    t = titulo.lower()
    if marcador == "@banco":
        if "jantar" in t:
            return "Furniture > Benches > Kitchen & Dining Benches"
        return "Furniture > Benches > Storage & Entryway Benches"
    if marcador == "@iluminacao":
        for padrao, cat in TITLE_KW[:6]:  # regras de lâmpada/pendente/luminária
            if re.search(padrao, t):
                return cat
        return "Home & Garden > Lighting > Lamps"
    return "Furniture"


def classificar(item_xml: str) -> str:
    m = RE_PRODUCT_TYPE.search(item_xml)
    product_type = (m.group(1) if m else "").replace("&gt;", ">")
    m = RE_TITLE.search(item_xml)
    titulo = m.group(1) if m else ""

    for chave, categoria in MAP:
        if chave.lower() in product_type.lower():
            return _refinar(categoria, titulo) if categoria.startswith("@") else categoria
    t = titulo.lower()
    for padrao, categoria in TITLE_KW:
        if re.search(padrao, t):
            return _refinar(categoria, titulo) if categoria.startswith("@") else categoria
    return "Furniture"


def injetar(m: re.Match) -> str:
    item = m.group(0)
    if "<g:google_product_category>" in item:
        return item
    categoria = escape(classificar(item))
    return item.replace(
        "</item>",
        f"<g:google_product_category>{categoria}</g:google_product_category></item>",
    )


def _status(url: str) -> int:
    """HTTP status da imagem; 0 para erro de rede (tratado como OK, por segurança)."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def corrigir_imagens(original: str) -> tuple[str, int]:
    """Substitui image_link quebrado (4xx definitivo) pela imagem OK de outra
    variação do mesmo produto (mesmo <link>)."""
    import concurrent.futures

    itens = re.findall(r"<item>.*?</item>", original, flags=re.S)
    pares = []
    for it in itens:
        link = RE_LINK.search(it)
        img = RE_IMAGE.search(it)
        if link and img:
            pares.append((link.group(1).strip(), img.group(1).strip()))

    urls = sorted({img for _, img in pares})
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        status = dict(zip(urls, ex.map(_status, urls)))

    ok_por_produto: dict[str, str] = {}
    for link, img in pares:
        if link not in ok_por_produto and status.get(img) == 200:
            ok_por_produto[link] = img

    trocas = 0
    for link, img in pares:
        st = status.get(img, 0)
        if 400 <= st < 500 and link in ok_por_produto:
            original = original.replace(
                f"<g:image_link>{img}</g:image_link>",
                f"<g:image_link>{ok_por_produto[link]}</g:image_link>",
            )
            trocas += 1
    return original, trocas


def main() -> None:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        original = resp.read().decode("utf-8")

    itens = original.count("<item>")
    if itens < 1000:
        raise SystemExit(f"Feed suspeito: só {itens} itens — abortando sem sobrescrever.")

    original, trocas = corrigir_imagens(original)
    print(f"{trocas} imagens quebradas substituídas por imagem do mesmo produto")

    enriquecido, n = re.subn(r"<item>.*?</item>", injetar, original, flags=re.S)
    if n != itens:
        raise SystemExit(f"Inconsistência: {itens} itens no feed, {n} processados.")

    with open(SAIDA, "w", encoding="utf-8") as f:
        f.write(enriquecido)
    print(f"{n} itens enriquecidos em {SAIDA}")


if __name__ == "__main__":
    main()
