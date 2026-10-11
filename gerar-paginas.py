#!/usr/bin/env python3
"""Gera uma pagina estatica por jogo (SEO) em `jogo/<id>.html` e atualiza o
`sitemap.xml`. Rode de novo sempre que o `jogos.json` mudar:

    python3 gerar-paginas.py

Cada pagina tem titulo/descricao/dados-estruturados proprios, a capa do jogo e
um botao "Jogar agora" que abre o jogo no app (rota `?jogo=<id>#/jogo/<id>`).
"""
import json, os, html, shutil

RAIZ = os.path.dirname(os.path.abspath(__file__))
SITE = 'https://emugames.kannonmtx.workers.dev'
CONSOLES = {
    'snes': 'Super Nintendo (SNES)',
    'arcade': 'Arcade (Neo Geo)',
}
OUT = os.path.join(RAIZ, 'jogo')


def esc(s):
    return html.escape(str(s or ''), quote=True)


def gerar():
    with open(os.path.join(RAIZ, 'jogos.json'), encoding='utf-8') as f:
        jogos = json.load(f)['jogos']

    # limpa e recria a pasta das paginas
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    # agrupa por console para os "outros jogos"
    por_console = {}
    for j in jogos:
        por_console.setdefault(j['console'], []).append(j)

    for j in jogos:
        gid = j['id']
        nome = j['nome']
        cons = CONSOLES.get(j['console'], j['console'])
        capa_rel = 'capas/' + (j.get('capa') or (gid + '.gif'))
        capa_abs = SITE + '/' + capa_rel
        # URL limpa: o Cloudflare redireciona `/jogo/x.html` -> `/jogo/x`
        # (307), entao canonical/sitemap/links apontam direto para a limpa.
        url = SITE + '/jogo/' + gid
        # Abre o jogo no app: volta pra RAIZ com `?jogo=<id>` (a home boota
        # nesse parametro e entra no jogo). `../` = raiz do site.
        jogar = '../?jogo=' + gid + '#/jogo/' + gid
        desc = j.get('descricao') or (nome + ' — clássico de ' + cons + '. Jogue online no navegador, de graça.')

        # "outros jogos" do mesmo console (links internos, bom pra SEO e pro usuario)
        outros = [o for o in por_console[j['console']] if o['id'] != gid][:8]
        outros_html = ''.join(
            '<a class="outro" href="./' + esc(o['id']) + '">'
            '<img src="../capas/' + esc(o.get('capa') or (o['id'] + '.gif')) + '" alt="' + esc(o['nome']) + '" loading="lazy">'
            '<span>' + esc(o['nome']) + '</span></a>'
            for o in outros
        )

        pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(nome)} — Jogar Online Grátis ({esc(cons)}) | EmuGames Lizzy</title>
<meta name="description" content="{esc(desc)[:300]}">
<meta name="robots" content="index, follow, max-image-preview:large">
<link rel="canonical" href="{esc(url)}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="EmuGames Lizzy">
<meta property="og:locale" content="pt_BR">
<meta property="og:title" content="{esc(nome)} — Jogar Online Grátis | EmuGames Lizzy">
<meta property="og:description" content="{esc(desc)[:300]}">
<meta property="og:url" content="{esc(url)}">
<meta property="og:image" content="{esc(capa_abs)}">
<link rel="stylesheet" href="./pagina.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "VideoGame",
  "name": "{esc(nome)}",
  "url": "{esc(url)}",
  "image": "{esc(capa_abs)}",
  "description": "{esc(desc)[:300]}",
  "gamePlatform": "{esc(cons)}",
  "applicationCategory": "Game",
  "operatingSystem": "Web Browser",
  "inLanguage": "pt-BR",
  "isPartOf": {{ "@type": "WebSite", "name": "EmuGames Lizzy", "url": "{SITE}/" }}
}}
</script>
</head>
<body>
<header><a href="../">🎮 EmuGames Lizzy</a><span>{esc(cons)}</span></header>
<main>
  <div class="capa"><img src="../{esc(capa_rel)}" alt="{esc(nome)}"></div>
  <h1>{esc(nome)}</h1>
  <p class="cons">{esc(cons)}</p>
  <a class="jogar" href="{esc(jogar)}">▶ Jogar agora</a>
  <p class="desc">{esc(desc)}</p>
  <p class="dica">Roda direto no navegador (celular ou PC), sem instalar nada. Tem controles de toque e salvar jogo.</p>
</main>
<footer>
  <h2>Outros jogos</h2>
  <div class="outros">{outros_html}</div>
  <a class="todos" href="../">Ver todos os jogos →</a>
</footer>
</body>
</html>
"""
        with open(os.path.join(OUT, gid + '.html'), 'w', encoding='utf-8') as f:
            f.write(pagina)

    # CSS compartilhado das paginas (1 arquivo, reusado por todas)
    with open(os.path.join(OUT, 'pagina.css'), 'w', encoding='utf-8') as f:
        f.write("""*{box-sizing:border-box;margin:0;padding:0}
body{background:#08090B;color:#F1F1EE;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;padding:16px;max-width:640px;margin:0 auto}
header{display:flex;justify-content:space-between;align-items:center;gap:10px;padding-bottom:14px;border-bottom:1px solid #2B2D33}
header a{color:#F1F1EE;font-weight:800;text-decoration:none}
header span{color:#9699A2;font-size:12px}
main{text-align:center;padding:22px 0}
.capa img{width:100%;max-width:420px;border-radius:16px;border:1px solid #2B2D33;display:block;margin:0 auto}
h1{font-size:clamp(22px,6vw,32px);margin-top:16px}
.cons{color:#9699A2;font-size:13px;margin-top:4px}
.jogar{display:inline-block;margin:18px 0;background:#E8E9E6;color:#0B0C0F;font-weight:800;text-decoration:none;padding:14px 28px;border-radius:999px;font-size:16px}
.desc{color:#D1D2D5;line-height:1.7;margin-top:8px;text-align:left}
.dica{color:#9699A2;font-size:12.5px;margin-top:12px}
footer{margin-top:26px;border-top:1px solid #2B2D33;padding-top:18px}
footer h2{font-size:13px;text-transform:uppercase;letter-spacing:.6px;color:#D1D2D5;margin-bottom:12px}
.outros{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:10px}
.outro{display:flex;flex-direction:column;gap:6px;text-decoration:none;color:#F1F1EE}
.outro img{width:100%;border-radius:10px;border:1px solid #2B2D33;aspect-ratio:1/1;object-fit:cover}
.outro span{font-size:11.5px;font-weight:700;line-height:1.2}
.todos{display:inline-block;margin-top:18px;color:#E8E9E6;font-weight:700;text-decoration:none}
""")

    # sitemap: home + uma entrada por jogo
    linhas = [f'  <url><loc>{SITE}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>']
    for j in jogos:
        linhas.append(f'  <url><loc>{SITE}/jogo/{j["id"]}</loc><priority>0.7</priority></url>')
    with open(os.path.join(RAIZ, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + '\n'.join(linhas) + '\n</urlset>\n')

    print(f"geradas {len(jogos)} paginas em jogo/  + sitemap com {len(jogos)+1} URLs")


if __name__ == '__main__':
    gerar()
