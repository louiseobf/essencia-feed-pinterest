# Feed Pinterest enriquecido — Essência Móveis

Gera diariamente `data/feed_pinterest.xml`: um espelho fiel do feed XML público
da Yampi com uma única adição — a tag `<g:google_product_category>` em cada
item, que a Yampi não fornece e que o Pinterest usa para distribuir os produtos
em busca, recomendações e compras (sem ela, o catálogo acumula o aviso 157).

- **Conectado no Pinterest como:** fonte de dados **principal** do catálogo
  (Catálogos → Fontes de dados)
- **URL usada pelo Pinterest:**
  `https://raw.githubusercontent.com/louiseobf/essencia-feed-pinterest/main/data/feed_pinterest.xml`
- **Feed original da Yampi (fonte):**
  `https://s3.amazonaws.com/images.yampi.me/xml/3845b0c0-9b21-11ea-a366-b5824485fb4c.xml`
- **Atualização:** GitHub Action diária às 05h (Brasília), após a Yampi
  regenerar o feed (~03h40); o Pinterest ingere às 08h
- **Rollback:** se algo der errado, basta editar a fonte de dados no Pinterest
  e voltar a URL para o feed original da Yampi acima
- **Conteúdo:** os mesmos dados já públicos no feed da loja; nada sensível

Também fica no repositório `data/pinterest_complementar.csv` (id → categoria
Google), gerado por `scripts/gerar_feed_complementar.py`, como referência.

Para rodar manualmente: aba **Actions** → *Atualizar feed complementar
Pinterest* → *Run workflow*.
