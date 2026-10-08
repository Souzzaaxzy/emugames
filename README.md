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
├── .assetsignore   ← exclui o `kof97.zip` grande (a ROM vai em partes)
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

Pronto — aparece na lista automaticamente. Detalhes em `jogos/README.md`.

## Abrir

```
index.html              → primeiro jogo do catálogo
index.html?jogo=topgear2 → jogo específico
```

Com 2+ jogos, o botão **☰ JOGOS** troca de jogo sem recarregar.

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

