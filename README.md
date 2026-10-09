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

Só existe **uma tela** (a home): cabeçalho, jogos recentes, botão de abrir do
aparelho, **busca**, **categorias** e **todos os jogos** — e, no fim da página,
o card de perfis (créditos). A antiga tela de **biblioteca** deixou de existir;
a lista completa vive na própria home.

```
/                        → home (URL limpa, sem hash)
/#/jogo/topgear2         → jogo específico
/?jogo=topgear2          → link antigo (redireciona para a rota `#/jogo/`)
```

Navegação de volta:

- **‹ JOGOS** (dentro do jogo) → **home**, para escolher outro jogo. Vale para
  jogos do catálogo e para os do aparelho.
- **Inatividade** (10 min sem toque) → home.

O botão de voltar usa `location.replace`, então a rota antiga não fica no
histórico — o botão "voltar" do aparelho sai do site em vez de reabrir o jogo.

O histórico de recentes é o mesmo `localStorage` (`emugames.recentes`), gravado
ao abrir o jogo; a home só o exibe.

### Home rolável

`#home` tem `min-height: 100dvh` (com fallback `100vh`) e empilha as áreas com
Flexbox. Como agora ela mostra a lista completa, a página **rola na vertical**;
os créditos são o último bloco (já não usam `margin-top: auto`). A faixa de
recentes e a barra de categorias rolam na horizontal.

### Grade de jogos

`#grid` usa **4 colunas fixas no celular** (como pedido) e, a partir de
`min-width: 640px`, passa para `repeat(auto-fill, minmax(140px, 1fr))` — assim
ela se repete e preenche a largura toda na tela do PC, de um lado ao outro.

### Categorias

As categorias ("Todos", "Nintendo", ...) ficam **abaixo da barra de pesquisa**,
dentro de um retângulo de bordas arredondadas (`#filtros`) que rola na
horizontal quando não cabem.

### Abrir um jogo do próprio aparelho

O botão **Abrir do meu aparelho** (na home) deixa o usuário escolher **qualquer
arquivo** do celular. O input **não tem `accept`**
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
fora (não depende do tamanho do vídeo). O vídeo só roda na home — para ao abrir
um jogo, para não roubar CPU do emulador.

### Animação do título (sincronizada com o vídeo)

O título **EmuGames Lizzy** tem uma animação em loop. Cada letra de "Lizzy"
**acende** em sequência — passa por **branco → preto → branco** — indo da
primeira letra até o **"Y"** e depois **voltando**. Quando a frente chega no Y,
acendem **5 estrelas** ao redor dele, que brilham por cerca de 2s. Depois o
ciclo recomeça.

O truque está na **sincronia**: o JS lê o `currentTime` e a `duration` do
`intro.mp4` e usa a fração do ciclo (0..1) a cada quadro. Ele **pinta a cor de
cada letra** direto (`rgb(...)`) e publica a mesma fração em `--p` no wrapper
das estrelas — então nada **nunca sai de fase com a gif**: a cada reinício do
vídeo a animação volta ao começo. O ciclo dura 3,08s (uma volta do vídeo).

O "preenchimento" é uma **frente** que anda pelo índice das letras: a letra sob
a frente fica preta e as vizinhas clareiam conforme ela se afasta — o que
produz o branco→preto→branco por letra. As fases (ida `0.08..0.55`, volta
`0.55..0.92`) e a largura da frente estão no topo da seção, no `index.html`.

As letras são montadas no JS: uma `<span class="letra">` por caractere, e a
última (o "Y") leva o id `letra-alvo`, que ancora as estrelas. As 5 estrelas
são posicionadas por deslocamentos relativos ao centro do Y (frações da caixa
dele) no array `ESTRELAS`. Dois cuidados que já quebraram a animação: as
estrelas são filhas **absolutas** do `<h1>`, então as medidas são **locais ao
h1** (não ao viewport); e o `scale()` do "pop" fica **em cada estrela**, não no
wrapper (o wrapper tem 0×0, então um `scale()` nele escalaria em torno da
origem do `h1` e **moveria** as estrelas).

Com `prefers-reduced-motion: reduce` a animação é escondida (CSS) e o loop de
`requestAnimationFrame` nem começa (JS).

## Recursos

- **PARAR** — desliga o emulador
- **Inatividade** — 3 min sem toque desliga sozinho
- **Fechar/voltar** — sai da aba e volta, o jogo reinicia sozinho
- **Controles de toque** — embaixo da tela (não cobrem o jogo), com dpad/botões maiores
- **Paisagem** — com o celular deitado o jogo ocupa a **tela cheia** e os controles
  ficam **+40px** maiores, flutuando sobre o jogo (o cabeçalho some e o PARAR vira
  um botão flutuante no canto)
- **Tom por console** — a cor do tema muda conforme o console (dentro da paleta)

## Tema visual

Identidade **monocromática** (preto profundo / branco-gelo / cinza-prata), com
toque japonês discreto. Todas as cores vivem em variáveis no `:root` do
`style.css` — os nomes (`--painel`, `--acento`, ...) foram mantidos de
propósito: como o CSS inteiro já os usa, trocar só os valores repinta o site
sem tocar em nenhuma regra de layout.

| variável | valor | uso |
|---|---|---|
| `--fundo` | `#08090B` | fundo principal |
| `--painel` | `#15161A` | superfície dos cards |
| `--painel2` | `#1B1C21` | superfície elevada |
| `--borda` | `#2B2D33` | borda discreta |
| `--texto` | `#F1F1EE` | branco principal |
| `--texto2` | `#D1D2D5` | branco secundário |
| `--fraco` | `#9699A2` | texto secundário |
| `--acento` | `#E8E9E6` | destaque (era azul `#1d4ed8`) |
| `--sobre-acento` | `#0B0C0F` | texto **sobre** o acento (acento claro) |

Como o acento passou de azul (escuro) para branco-gelo (claro), todo lugar que
usa `--acento` **como fundo** também troca a cor do texto para
`--sobre-acento` — senão o texto sumiria.

**As capas dos jogos continuam coloridas**: nenhum filtro global é aplicado. O
`#game` (palco do emulador) tem `filter: none` e `mix-blend-mode: normal`,
verificado por medição.

Transições: `--t-rapida` (130ms) e `--t-media` (190ms) com `--curva`
(`cubic-bezier`). Priorizam `opacity`/`transform`. Há
`@media (prefers-reduced-motion: reduce)` desligando tudo para quem pede menos
movimento.

### Brilhos dentro das caixas

Os cards (jogos e recentes), os perfis, a busca, as categorias, o aviso de
vazio, o erro e o painel do controle levam um padrão de **símbolos** (⊹ ⋆ ✩ ⭒
✧ ˖) no fundo. É um único `background-image` — um SVG em `data:` na variável
`--brilho` (no fim do `style.css`), repetido a cada `170px`. Fica **atrás** do
conteúdo, não intercepta toque (não é pseudo-elemento) e não muda o layout. O
**fundo da página não** usa o padrão.

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
