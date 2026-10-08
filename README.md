# TOPGEAR — emulador multi-jogo no webview

Roda jogos de console dentro do webview do WhatsApp, via
[EmulatorJS](https://emulatorjs.org) (cores WebAssembly).

## Estrutura

```
emugames/                    <- ESTE repositório (o site)
├── index.html      ← player + CATÁLOGO (tela inicial com os jogos)
├── style.css
├── jogos.json      ← catálogo (o bot guarda uma cópia: o `!arcade` lê dela)
├── wrangler.jsonc  ← config de publicação (Cloudflare Workers)
├── _headers        ← COOP/COEP (libera SharedArrayBuffer → núcleo com threads)
├── .assetsignore   ← exclui `.git` e o `kof97.zip` grande (a ROM vai em partes)
├── capas/          ← capas dos jogos (GIF)
├── neogeo.zip      ← BIOS do Neo Geo (FBNeo)
└── jogos/
    ├── snes/
    └── arcade/
```

> **Este repo é o SITE.** Ele era uma pasta dentro do repositório do bot
> (`dados/emugames/`) e foi separado para o bot não carregar 113 MB em cada
> `!atualizar`. O bot guarda só o `jogos.json` (o catálogo que o menu lê) e a
> URL pública.

### ⚠️ Os DOIS `jogos.json`

| onde | para que |
|---|---|
| **aqui** (`emugames/jogos.json`) | o site mostra a lista de jogos |
| **no bot** (`dados/emugames/jogos.json`) | o `!arcade`/menus/cards montam a lista |

**Ao adicionar um jogo, atualize os dois** — senão o site mostra e o comando não
(ou o contrário).

## Adicionar um jogo

1. Coloque a ROM em `jogos/<console>/`
2. Adicione uma linha no `jogos.json`

## Telas e rotas

A **home** é um launcher de uma tela só (cabe na viewport, sem rolagem
vertical): cabeçalho, jogos recentes, card da biblioteca e os créditos no
rodapé. A **biblioteca** é a tela separada com a pesquisa, os filtros e todos
os jogos.

```
/                        → home (URL limpa, sem hash)
/#/biblioteca            → biblioteca completa
/#/jogo/topgear2         → jogo específico
/?jogo=topgear2          → link antigo (redireciona para a rota `#/jogo/`)
```

Navegação de volta:

- **‹ JOGOS** (dentro do jogo) → **biblioteca** (`#/biblioteca`), para escolher
  outro jogo direto. Vale para jogos do catálogo e para os do aparelho.
- **‹ INÍCIO** (na biblioteca) → **home**, com a URL limpa (`/`).
- **Inatividade** (10 min sem toque) → home.

Os dois usam `location.replace`, então a rota antiga não fica no histórico — o
botão "voltar" do aparelho sai do site em vez de reabrir o jogo.

O histórico de recentes é o mesmo `localStorage` (`emugames.recentes`), gravado
ao abrir o jogo; a home só o exibe.

### Home sem rolagem

`#home` tem `height: 100dvh` (com fallback `100vh`) e empilha as áreas com
Flexbox; os créditos sobem para o rodapé via `margin-top: auto`. Em telas baixas
(`max-height: 700px` / `560px`) os espaços e os cards encolhem — nada é
escondido. A faixa de recentes rola na horizontal, nunca na vertical.

### Cards de perfil (créditos)

Ficam **um embaixo do outro** (Kannon/Criador primeiro), retangulares e com o
conteúdo centralizado. Eles **crescem para absorver a sobra** da home
(`#creditos { flex: 1 1 auto }` + `.perfil { flex: 1 1 0 }`): é isso que
preenche o vazio em vez de deixar buraco no rodapé.

Duas armadilhas resolvidas aqui:

- `min-height: min-content` no `.perfil` — sem isso o flex encolhia o card
  **abaixo do conteúdo** em telas baixas e ele vazava para fora da tela.
- `white-space: nowrap` no nome — o nome do Kannon é maior; quebrando, o card
  dele ficava mais alto que o do M06.

Em telas com pouca altura (`max-height: 900/620px`) os vãos, o vídeo e os cards
de recentes encolhem para a home caber inteira.

### Preview do link (Open Graph)

`preview.jpg` é **1.91:1 (1536×804)** — a proporção do preview **grande** do
WhatsApp. Com a imagem em 3:2 (1536×1024) ele cortava ou usava o card pequeno.
O corte manteve o topo: o assunto da foto está todo nos 512px de cima e a
metade de baixo é quase preta.

Para trocar a imagem: gere em **1.91:1** (ex.: 1200×630) e atualize
`og:image:width`/`height`.

### PC (telas largas)

Em PC a janela é muito mais larga que um celular. Duas regras resolvem:

- **Teto de 620px** no conteúdo (`#home > *:not(.cabeca)`, `#biblioteca > *`):
  sem ele os cards e botões esticavam até ~1900px. O `.cabeca` fica de fora
  porque o vídeo mora dentro dele e precisa sangrar.
- **Vídeo com `object-fit: fill`**: a faixa do topo é muito mais larga que o
  vídeo (16:9). Com `cover` as laterais eram **cortadas**; com `fill` o quadro
  inteiro aparece, só um pouco achatado.

A sangria do vídeo usa `calc(100% + 2 * --pad-lado)` + `margin-left` negativo —
não `100vw`, que inclui a barra de rolagem e criava overflow horizontal.

Em laptops (`min-width: 900px` e `max-height: 800px`) o vídeo e os vãos
encolhem para a home caber inteira.

> ⚠️ Se mudar o `padding` lateral do `#home`, mude também `--pad-lado`: é ela
> que o vídeo cancela para encostar nas bordas. (Já aconteceu de o padding de
> paisagem virar 6px e a variável ficar 8px — sobrava overflow de 2px.)

### Abrir um jogo do próprio aparelho

O botão **Abrir do meu aparelho** (abaixo do da biblioteca, na home) deixa o
usuário escolher **qualquer arquivo** do celular. O input **não tem `accept`**
de propósito: com o filtro, o seletor do Android esconde/desabilita ROMs que
ele não reconhece (quase toda ROM chega como `application/octet-stream`). O
console é detectado **depois**, pela extensão do arquivo (`.sfc` → `snes`,
`.md` → `segaMD`, `.gba` → `gba`, …).

O arquivo é guardado no **IndexedDB** (aguenta ROMs grandes) e o emulador o
carrega por uma URL de objeto (`blob:`), o mesmo caminho que as “partes” do
`kof97` já usam.

Fluxo: escolhe → grava no IndexedDB → `?arquivo=<nome>#/jogo/local:<nome>` →
o boot monta o emulador. O jogo aparece nos **recentes** da home (sem capa, com
o emoji do console) e reabre por ali; o `?arquivo=` sai da URL logo depois do
boot, então voltar/recarregar continua funcionando.

> ⚠️ O hash precisa do prefixo **`local:`** (`#/jogo/local:<nome>`). Sem ele a
> rota parece um jogo do catálogo e o site responde *“não está no catálogo”*.

> A detecção por extensão pode errar em arquivos fora do padrão (ex.: um `.bin`
> de Mega Drive vs. de PlayStation). `.zip`/`.7z` caem em `arcade`, que exige o
> romset completo **e** a BIOS.

### Intro em vídeo

`intro.mp4` (540×300, H.264, ~260 KB) fica no topo da home com bordas
arredondadas, mudo, em loop e `playsinline`. O título **atravessa** a base do
vídeo: `margin-top: -0.55em` no `h1` põe metade dele sobre o vídeo e metade
fora (não depende do tamanho do vídeo). O vídeo só roda na home — para na
biblioteca e ao abrir um jogo, para não roubar CPU do emulador.

## Recursos

- **PARAR** — desliga o emulador
- **Inatividade** — 3 min sem toque desliga sozinho
- **Fechar/voltar** — sai da aba e volta, o jogo reinicia sozinho
- **Controles de toque** — embaixo da tela (não cobrem o jogo), com dpad/botões maiores
- **Paisagem** — com o celular deitado o jogo ocupa a **tela cheia** e os controles
  ficam **+40px** maiores, flutuando sobre o jogo (o cabeçalho some e o PARAR vira
  um botão flutuante no canto)
- **Cores por console** — a cor do tema muda conforme o console

## Hospedagem

Servido por **Cloudflare Workers** (static assets) — é o único host usado.
Config em `wrangler.jsonc` (`assets.directory` = `.`, ou seja, a RAIZ deste
repo); deploy com `wrangler deploy`.

### Limite de 25 MiB por arquivo (importante)

O Cloudflare limita **cada asset a 25 MiB** — e se algum arquivo passar disso,
**o deploy inteiro falha**. Foi o que acontecia com o `kof97.zip` (27,6 MiB).

Por isso a ROM grande vai em **PARTES** (`kof97.zip.p1/.p2`, ~13,8 MiB cada):

1. o **zip inteiro** fica no `.assetsignore` e **nao** sobe;
2. as **partes** sobem normalmente e o player as baixa e **remonta num Blob**;
3. no `jogos.json`, o jogo leva o campo **`"partes": ["kof97.zip.p1", ...]`**.

Assim tudo sai do **mesmo host** do site. Ha teste que falha se uma ROM acima do
limite nao estiver dividida, se alguma parte passar de 25 MiB, ou se as partes
nao somarem o zip inteiro.

#### O `.assetsignore` precisa excluir o `.git`

O `wrangler` le a **raiz** do repositorio como `assets.directory` e **nao ignora
o `.git` sozinho**. O pack do `.git` passa de 100 MiB e guarda o blob do
`kof97.zip` (27,6 MiB) — entao, sem esta linha no `.assetsignore`, o deploy morre
na etapa *"Building list of assets"* com:

```
[ERROR] Asset too large.
  ...found a file /opt/buildhome/repo/.git/objects/... with a size of 27.6 MiB
```

Por isso o `.assetsignore` comeca com:

```
.git
.wrangler
node_modules
```

### Cloudflare

`wrangler.jsonc` (`assets.directory` = `.`) + `wrangler deploy`.
No painel: *Framework* None, *Build command* **vazio**.

### ⚠️ Deploy MANUAL — o site NÃO atualiza sozinho do `main`

O Worker é um **deploy manual**. Adicionar jogo, ROM, capa ou editar o
`jogos.json` **não** muda o site no ar até rodar o deploy.
Se um comando novo abrir o site e aparecer *"Registre um jogo no jogos.json"* ou
*"Jogo X não está no catálogo"*, quase sempre é isto: **o site no ar está com o
catálogo antigo**.

```bash
# na raiz do projeto (uma vez: npm i -g wrangler  ou  npx wrangler)
npx wrangler deploy
```

Para conferir o que está no ar sem abrir o navegador:

```bash
curl -s https://emugames.kannonmtx.workers.dev/jogos.json | grep -c '"id"'
# confira com a contagem local:
python3 -c "import json;print(len(json.load(open('jogos.json'))['jogos']))"
```

> O `!arcade` e os comandos `!<jogo>` leem o **catálogo local** (do repositório)
> só para montar o card e a URL; quem serve a ROM e o `jogos.json` de verdade é
> o **site**. Por isso o card aparece mesmo com o site desatualizado — mas o jogo
> não abre até o deploy.
