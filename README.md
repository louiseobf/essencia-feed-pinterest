# Feed complementar Pinterest — Essência Móveis

Gera diariamente o arquivo `data/pinterest_complementar.csv` com o campo
`google_product_category` para todos os produtos do catálogo da Essência Móveis
no Pinterest, a partir do feed XML público da Yampi (que não inclui esse campo).

- **Conectado no Pinterest como:** fonte de dados complementar do catálogo
  (Catálogos → Fontes de dados → Fonte de dados complementar)
- **URL usada pelo Pinterest:**
  `https://raw.githubusercontent.com/louiseobf/essencia-feed-pinterest/main/data/pinterest_complementar.csv`
- **Atualização:** GitHub Action diária às 05h (Brasília), após a Yampi
  regenerar o feed principal (~03h40)
- **Conteúdo:** apenas ID do produto e categoria Google — dados já públicos no
  feed da loja; nada sensível

Para rodar manualmente: aba **Actions** → *Atualizar feed complementar
Pinterest* → *Run workflow*.
