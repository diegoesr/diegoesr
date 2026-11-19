"""Genera dark_mode.svg y light_mode.svg: retrato ASCII + ficha estilo neofetch con datos de GitHub.

Local:          python today.py                     (sin token usa la API pública; "Contributed" queda en ?)
Con token:      ACCESS_TOKEN=xxx python today.py
GitHub Actions: lo ejecuta .github/workflows/update.yml todos los días.
"""
import datetime
import os
from xml.sax.saxutils import escape

import requests
from dateutil.relativedelta import relativedelta

USER = os.environ.get("USER_NAME", "diegoesr")
TOKEN = os.environ.get("ACCESS_TOKEN")
API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json", **({"Authorization": f"bearer {TOKEN}"} if TOKEN else {})}

# "Uptime" cuenta desde esta fecha. Ahora es la fecha en que creaste tu cuenta de GitHub;
# cámbiala por tu fecha de nacimiento si quieres que muestre tu edad, como en el original.
UPTIME_DESDE = datetime.date(2021, 4, 28)

ANCHO = 60          # caracteres por línea de la ficha
COL_IZQ = 34        # ancho de la columna izquierda en las líneas de estadísticas
CHAR_W = 8.8        # ancho de un carácter de Consolas a 16px
LINE_H = 20

TEMAS = {
    "dark_mode.svg": dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", cc="#616e7f"),
    "light_mode.svg": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", cc="#c2cfde"),
}


# ---------------------------------------------------------------- datos
def uptime():
    d = relativedelta(datetime.date.today(), UPTIME_DESDE)
    plural = lambda n, s, p: f"{n} {s if n == 1 else p}"
    return f"{plural(d.years, 'año', 'años')}, {plural(d.months, 'mes', 'meses')}, {plural(d.days, 'día', 'días')}"


def get(url, **kw):
    r = requests.get(url, headers=HEADERS, timeout=30, **kw)
    r.raise_for_status()
    return r.json()


def github_stats():
    commits = get(f"{API}/search/commits", params={"q": f"author:{USER}", "per_page": 1})["total_count"]
    if TOKEN:
        q = """query($login: String!) { user(login: $login) {
            followers { totalCount }
            repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount nodes { stargazerCount } }
            repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
        }}"""
        r = requests.post(f"{API}/graphql", headers=HEADERS, timeout=30,
                          json={"query": q, "variables": {"login": USER}})
        r.raise_for_status()
        body = r.json()
        if "errors" in body:
            raise RuntimeError(body["errors"])
        u = body["data"]["user"]
        return dict(repos=u["repositories"]["totalCount"],
                    contributed=u["repositoriesContributedTo"]["totalCount"],
                    stars=sum(n["stargazerCount"] for n in u["repositories"]["nodes"]),
                    commits=commits, followers=u["followers"]["totalCount"])
    # Sin token: API REST pública (no expone "repos a los que contribuiste").
    user = get(f"{API}/users/{USER}")
    repos = get(f"{API}/users/{USER}/repos", params={"per_page": 100, "type": "owner"})
    return dict(repos=user["public_repos"], contributed="?",
                stars=sum(r["stargazers_count"] for r in repos),
                commits=commits, followers=user["followers"])


# ---------------------------------------------------------------- maquetado
def fmt(v):
    return f"{v:,}" if isinstance(v, int) else str(v)


def puntos(n):
    """Relleno de puntos entre clave y valor, como en neofetch."""
    if n <= 0:
        return ""
    if n <= 2:
        return " " * n
    return " " + "." * (n - 2) + " "


def kv(key, value, width=ANCHO, prefix=". ", extra=()):
    """Línea '. Key: ...... value' alineada a `width`. `extra` = segmentos tras el valor."""
    value = fmt(value)
    largo_extra = sum(len(t) for t, _ in extra)
    relleno = width - len(prefix) - len(key) - 1 - len(value) - largo_extra
    return [(prefix, "cc"), (key, "key"), (":", None), (puntos(relleno), "cc"), (value, "value"), *extra]


def titulo(texto):
    return [(texto, None), (" -" + "—" * (ANCHO - len(texto) - 5) + "-—-", None)]


def lineas_ficha(s):
    vacio = [(". ", "cc")]
    stats_1 = kv("Repos", s["repos"], COL_IZQ,
                 extra=[(" {", None), ("Contributed", "key"), (": ", None), (fmt(s["contributed"]), "value"), ("}", None)])
    stats_1 += [(" | ", None)] + kv("Stars", s["stars"], ANCHO - COL_IZQ - 3, prefix="")
    stats_2 = kv("Commits", s["commits"], COL_IZQ)
    stats_2 += [(" | ", None)] + kv("Followers", s["followers"], ANCHO - COL_IZQ - 3, prefix="")
    return [
        titulo("diego@esparza"),
        kv("OS", "Windows 11"),
        kv("Uptime", uptime()),
        kv("Host", "Facultad de Ingeniería, UNAM"),
        kv("Kernel", "Desarrollador Web Full Stack"),
        kv("Lab", "iOS Development Lab"),
        kv("IDE", "VSCode, Xcode"),
        vacio,
        kv("Languages.Code", "JavaScript, TypeScript, Python, Swift"),
        kv("Languages.Web", "HTML, CSS, Tailwind, SQL"),
        kv("Languages.Real", "Español, Inglés"),
        vacio,
        kv("Frameworks", "React, Node.js, Bootstrap"),
        kv("Databases", "MySQL, PostgreSQL"),
        [],
        titulo("- Contact"),
        kv("Email", "diego_esparza02@outlook.com"),
        kv("LinkedIn", "diego-esparza-rodriguez-970a19210"),
        kv("Instagram", "diego_vstheworld"),
        kv("Portfolio", "portafolio2026-six.vercel.app"),
        [],
        titulo("- GitHub Stats"),
        stats_1,
        stats_2,
    ]


def construir_svg(ascii_filas, ficha, t):
    ascii_cols = max(len(f) for f in ascii_filas)
    x_ficha = round(15 + ascii_cols * CHAR_W + 30)
    ancho_svg = round(x_ficha + ANCHO * CHAR_W + 25)
    filas = max(len(ascii_filas), len(ficha))
    alto_svg = 30 + filas * LINE_H
    y_ficha = 30 + (filas - len(ficha)) // 2 * LINE_H   # centra la ficha junto al retrato

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho_svg}px" height="{alto_svg}px" '
        f'font-family="ConsolasFallback,Consolas,monospace" font-size="16px">',
        "<style>",
        "@font-face { font-family: ConsolasFallback; src: local('Consolas'); }",
        f".key {{fill: {t['key']};}} .value {{fill: {t['value']};}} .cc {{fill: {t['cc']};}}",
        "text, tspan {white-space: pre;}",
        "</style>",
        f'<rect width="{ancho_svg}px" height="{alto_svg}px" fill="{t["bg"]}" rx="15"/>',
        f'<text x="15" y="30" fill="{t["text"]}">',
    ]
    for i, fila in enumerate(ascii_filas):
        out.append(f'<tspan x="15" y="{30 + i * LINE_H}">{escape(fila)}</tspan>')
    out.append("</text>")
    out.append(f'<text x="{x_ficha}" y="{y_ficha}" fill="{t["text"]}">')
    for i, segmentos in enumerate(ficha):
        partes = "".join(
            f'<tspan class="{c}">{escape(txt)}</tspan>' if c else escape(txt) for txt, c in segmentos if txt
        )
        out.append(f'<tspan x="{x_ficha}" y="{y_ficha + i * LINE_H}">{partes}</tspan>')
    out += ["</text>", "</svg>", ""]
    return "\n".join(out)


def main():
    aqui = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(aqui, "ascii.txt"), encoding="utf-8") as f:
        ascii_filas = f.read().split("\n")
    stats = github_stats()
    print("Stats:", stats)
    ficha = lineas_ficha(stats)
    for archivo, tema in TEMAS.items():
        with open(os.path.join(aqui, archivo), "w", encoding="utf-8") as f:
            f.write(construir_svg(ascii_filas, ficha, tema))
        print("Escrito", archivo)


if __name__ == "__main__":
    main()
