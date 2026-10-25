#!/usr/bin/env python3
"""Anclame - fase 1. Genera data/directory.csv y el sitio estatico en docs/.

Entrada: el artefacto de JavaScript servido por aiwritteninputs.vercel.app,
que lleva el corpus incrustado como literal de plantilla.
Salida: metadatos unicamente. El texto de las respuestas nunca se reproduce.
"""
import csv, hashlib, html, io, json, os, shutil, sys

FUENTE = "QuestionnaireViewer-D3o4zISX.js"
RAIZ = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(RAIZ, "data")
DOCS = os.path.join(RAIZ, "docs")
csv.field_size_limit(10 ** 9)

CABECERA = "ID,Organization,Stakeholder category,Region"
SERVIDOR = {
    "url": "https://aiwritteninputs.vercel.app/assets/QuestionnaireViewer-D3o4zISX.js",
    "bytes": 18461048,
    "sha256": "bc148c0f59ffa7c252048eb28aa386c5ed76122e46ed49fafa3ce316df4919ed",
}
CANON = {
    "civil society": "Civil Society",
    "academia": "Academia",
    "private sector": "Private Sector",
    "international organisation": "International Organisation",
    "international organization": "International Organisation",
    "government": "Government",
    "technical community": "Technical Community",
}


# --------------------------------------------------------------------------
# Extraccion
# --------------------------------------------------------------------------
def extraer_csv(ruta):
    """Recorre el literal de plantilla aplicando las reglas de escape de ECMAScript."""
    s = open(ruta, encoding="utf-8").read()
    h = s.find(CABECERA)
    if h < 0:
        sys.exit("No se encuentra la cabecera del corpus en " + ruta)
    i = s.rfind("`", 0, h) + 1
    out, n = [], len(s)
    while i < n:
        c = s[i]
        if c == "`":
            break
        if c != "\\":
            out.append(c)
            i += 1
            continue
        i += 1
        e = s[i]
        if e in "ntrbfv0":
            out.append({"n": "\n", "t": "\t", "r": "\r", "b": "\b",
                        "f": "\f", "v": "\v", "0": "\0"}[e])
            i += 1
        elif e == "u":
            if s[i + 1] == "{":
                j = s.index("}", i + 2)
                out.append(chr(int(s[i + 2:j], 16)))
                i = j + 1
            else:
                out.append(chr(int(s[i + 1:i + 5], 16)))
                i += 5
        elif e == "x":
            out.append(chr(int(s[i + 1:i + 3], 16)))
            i += 3
        elif e == "\n":
            i += 1
        else:
            out.append(e)
            i += 1
    return "".join(out).lstrip("\ufeff")


def reparar(s):
    """Deshace la doble codificacion UTF-8 si el resultado es valido."""
    if not any(c in s for c in ("Ã", "Â", "â€")):
        return s, False
    try:
        r = s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s, False
    return (r, True) if r != s else (s, False)


# --------------------------------------------------------------------------
# Directorio
# --------------------------------------------------------------------------
CAMPOS = ["ID", "Organization", "StakeholderCategory", "Region",
          "OrganizationAsStored", "EncodingRepaired", "StakeholderCategoryAsStored",
          "QuestionsAnswered", "ResponseCharacters", "FrenchReplicaRecord"]


def construir(texto):
    filas = list(csv.reader(io.StringIO(texto)))
    datos = filas[1:]
    registros = []
    for f in datos:
        ident, org_alm, cat_alm, region = f[0], f[1], f[2], f[3]
        org, marca = reparar(org_alm)
        resp = f[4:]
        registros.append({
            "ID": ident,
            "Organization": org,
            "StakeholderCategory": CANON.get(cat_alm.strip().lower(), cat_alm.strip()),
            "Region": region,
            "OrganizationAsStored": org_alm,
            "EncodingRepaired": "yes" if marca else "no",
            "StakeholderCategoryAsStored": cat_alm,
            "QuestionsAnswered": sum(1 for r in resp if r.strip()),
            "ResponseCharacters": sum(len(r) for r in resp),
            "FrenchReplicaRecord": f"https://aidialoguereport.org/explorer/{ident}/",
        })
    registros.sort(key=lambda r: int(r["ID"]))
    return registros, len(filas[0])


# --------------------------------------------------------------------------
# Sitio
# --------------------------------------------------------------------------
CSS = open(os.path.join(RAIZ, "theme.css"), encoding="utf-8").read()


def es_num(n):
    return f"{n:,}".replace(",", ".")


def marco(titulo, cuerpo, prof=0, desc="", marca=True):
    base = "../" * prof if prof else "./"
    marca_html = (f'<span class="name"><a href="{base}">Anclame</a></span>' if marca else "")
    d = f'<meta name="description" content="{html.escape(desc)}">' if desc else ""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title>
{d}
<link rel="stylesheet" href="{base}style.css">
</head>
<body>
<div class="wrap">
<header class="site">
  {marca_html}
  <nav>
    <a href="{base}">Inicio</a>
    <a href="{base}register.html">Lista</a>
    <a href="{base}method.html">Procedencia</a>
    <a href="{base}privacy.html">Privacidad</a>
  </nav>
</header>
{cuerpo}
<footer>
<p>Los metadatos de este registro proceden del corpus publicado por el Diálogo Global
sobre Gobernanza de la IA. El texto de las aportaciones no se reproduce aquí.</p>
<p>Metadata in this register is derived from the corpus published by the Global Dialogue
on AI Governance. The text of the contributions is not reproduced here.</p>
<p><a href="{base}privacy.html">Privacidad y retirada</a> &middot;
<a href="{base}method.html">Procedencia</a></p>
</footer>
</div>
</body>
</html>
"""


def pagina_indice(regs, cols):
    por_region, por_cat, por_almacenada = {}, {}, {}
    reparados = 0
    for r in regs:
        por_region[r["Region"]] = por_region.get(r["Region"], 0) + 1
        por_cat[r["StakeholderCategory"]] = por_cat.get(r["StakeholderCategory"], 0) + 1
        k = r["StakeholderCategoryAsStored"]
        por_almacenada[k] = por_almacenada.get(k, 0) + 1
        if r["EncodingRepaired"] == "yes":
            reparados += 1

    fr = "".join(f"<tr><td>{html.escape(k)}</td><td class='num'>{v}</td></tr>"
                 for k, v in sorted(por_region.items(), key=lambda x: -x[1]))

    fc = ""
    for cat, total in sorted(por_cat.items(), key=lambda x: -x[1]):
        variantes = sorted((k, v) for k, v in por_almacenada.items()
                           if CANON.get(k.strip().lower(), k.strip()) == cat)
        detalle = "; ".join(
            f"{'sin variación' if k == cat else html.escape(repr(k))} &times; {v}"
            for k, v in variantes)
        fc += (f"<tr><td>{html.escape(cat)}</td><td class='num'>{total}</td>"
               f"<td class='mono'>{detalle}</td></tr>")

    cuerpo = f"""
<div class="hero">
  <span class="sea" aria-hidden="true">
    <svg viewBox="0 0 2400 18" preserveAspectRatio="none">
      <path d="M0 9q150 -5.5 300 0t300 0t300 0t300 0t300 0t300 0t300 0t300 0"/>
    </svg>
  </span>
  <span class="mark">Anclame<span class="rig"><span class="chain"></span>
    <svg class="anchor" width="19" height="27" viewBox="0 0 22 31" fill="none"
         stroke="currentColor" stroke-width="1.1" stroke-linecap="round" aria-hidden="true">
      <circle cx="11" cy="3.6" r="2.6"/>
      <path d="M11 6.2V27.4"/>
      <path d="M6 10.4h10"/>
      <path d="M2.4 18.6c0 5 3.9 8.8 8.6 8.8s8.6-3.8 8.6-8.8"/>
    </svg></span></span>
</div>

<h1>Que una aportación se pueda encontrar, citar y volver a leer</h1>
<p class="lead">{es_num(len(regs))} personas y organizaciones de todo el mundo respondieron a la
convocatoria del Diálogo Global sobre Gobernanza de la IA de Naciones Unidas. Sus textos
están publicados, pero no tienen dirección propia, no aparecen en los buscadores y no se
pueden citar. Anclame le da a cada uno una dirección estable y documenta de dónde sale
cada dato.</p>
<p class="small">Esto no es un sitio oficial de Naciones Unidas ni una crítica a quienes
participaron. Es un registro para que su trabajo se pueda encontrar.</p>
<p class="en">{len(regs):,} people and organisations around the world answered the call of
the UN Global Dialogue on AI Governance. Their texts are published, but have no address of
their own, do not appear in search engines and cannot be cited. Anclame gives each one a
stable address and documents where every figure comes from. This is not an official UN
site, nor a criticism of those who took part.</p>

<h2>Una dirección por aportación</h2>
<p>Cada registro tiene aquí una dirección propia y estable, de la forma
<span class="mono">/entry/669/</span>, que se puede citar y a la que se puede volver. En el
sitio oficial no la tiene: el corpus entero vive dentro de un marco cuyo contenido está
marcado para que los buscadores no lo indexen.</p>
<p class="en">On the official site there is none: the whole corpus lives inside a frame
whose contents are marked so that search engines will not index them.</p>
<p><a href="register.html">Ver la lista completa</a></p>

<h2>Cuántas hay</h2>
<p>El fichero que sirve la página contiene {es_num(len(regs))} registros, con {es_num(len(regs))}
identificadores distintos y ninguno repetido. Las preguntas frecuentes del sitio oficial
hablan de 1.532 aportaciones. La diferencia no está explicada en ninguna parte.</p>
<div class="figures">
  <div><div class="n">{es_num(len(regs))}</div><div class="lab">registros en el fichero<br>records in the file</div></div>
  <div><div class="n off">1.532</div><div class="lab">aportaciones declaradas<br>contributions stated</div></div>
  <div><div class="n">{reparados}</div><div class="lab">nombres con la codificación dañada<br>names with broken encoding</div></div>
</div>

<h2>Por región · By region</h2>
<div class="scroll"><table>
<thead><tr><th>Región</th><th class="num">Registros</th></tr></thead>
<tbody>{fr}</tbody></table></div>

<h2>Por categoría · By stakeholder category</h2>
<p class="small">Las categorías no están normalizadas en el origen. Las variantes con
espacios finales, y la forma <span class="mono">International Organization</span> frente a
<span class="mono">International Organisation</span>, quedan fuera de los filtros del visor
oficial. Aquí se recuentan juntas y se muestra la forma tal como está almacenada.</p>
<div class="scroll"><table>
<thead><tr><th>Categoría</th><th class="num">Registros</th><th>Formas almacenadas</th></tr></thead>
<tbody>{fc}</tbody></table></div>

<h2>Qué hay y qué no hay aquí</h2>
<p>Este registro contiene metadatos: identificador, organización, categoría, región,
cuántas preguntas contestó cada aportación y cuántos caracteres ocupa la respuesta. No
contiene el texto de las respuestas, y no va a contenerlo sin el consentimiento de quien
lo escribió.</p>
<p class="en">This register holds metadata only. It does not hold the text of the answers,
and will not without the consent of whoever wrote them.</p>
<p><a href="method.html">Cómo se ha obtenido</a></p>
"""
    return marco("Anclame · Registro de aportaciones escritas", cuerpo, 0, marca=False, desc=
                 "Registro citable de las 1.534 aportaciones escritas al Diálogo Global "
                 "sobre Gobernanza de la IA de Naciones Unidas.")


def pagina_lista(regs):
    filas = "".join(
        f'<tr data-r="{html.escape(r["Region"])}" data-c="{html.escape(r["StakeholderCategory"])}">'
        f'<td class="num"><a href="entry/{r["ID"]}/">{r["ID"]}</a></td>'
        f'<td>{html.escape(r["Organization"])}'
        f'{" <span class=repaired title=\"codificación reparada\">&#9873;</span>" if r["EncodingRepaired"] == "yes" else ""}</td>'
        f'<td>{html.escape(r["StakeholderCategory"])}</td>'
        f'<td>{html.escape(r["Region"])}</td></tr>'
        for r in regs)
    regiones = sorted({r["Region"] for r in regs})
    cats = sorted({r["StakeholderCategory"] for r in regs})
    opt_r = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in regiones)
    opt_c = "".join(f'<option value="{html.escape(x)}">{html.escape(x)}</option>' for x in cats)

    cuerpo = f"""
<h1>Lista completa</h1>
<p class="small">All {len(regs):,} records</p>
<p class="note">El símbolo &#9873; marca los nombres cuya codificación estaba dañada en el
origen y aparece aquí reparada. La forma almacenada se conserva en la ficha de cada uno.</p>
<div class="filters">
  <input id="q" type="search" placeholder="Buscar organización · Search organisation" aria-label="Buscar organización">
  <select id="fr" aria-label="Región"><option value="">Todas las regiones</option>{opt_r}</select>
  <select id="fc" aria-label="Categoría"><option value="">Todas las categorías</option>{opt_c}</select>
</div>
<p id="tally">{es_num(len(regs))} registros</p>
<div class="scroll"><table id="t">
<thead><tr><th class="num">ID</th><th>Organización</th><th>Categoría</th><th>Región</th></tr></thead>
<tbody>{filas}</tbody></table></div>
<script>
(function(){{
  var q=document.getElementById('q'),fr=document.getElementById('fr'),
      fc=document.getElementById('fc'),tally=document.getElementById('tally'),
      rows=[].slice.call(document.querySelectorAll('#t tbody tr'));
  function apply(){{
    var t=q.value.trim().toLowerCase(),r=fr.value,c=fc.value,n=0;
    rows.forEach(function(row){{
      var ok=(!r||row.dataset.r===r)&&(!c||row.dataset.c===c)&&
             (!t||row.cells[1].textContent.toLowerCase().indexOf(t)>-1);
      row.hidden=!ok; if(ok)n++;
    }});
    tally.textContent=n.toLocaleString('es-ES')+(n===1?' registro':' registros');
  }}
  [q,fr,fc].forEach(function(el){{el.addEventListener('input',apply)}});
}})();
</script>
"""
    return marco("Lista completa · Anclame", cuerpo, 0)


ETIQUETAS = [
    ("ID", "Identificador", "Identifier"),
    ("Organization", "Organización", "Organisation"),
    ("StakeholderCategory", "Categoría", "Stakeholder category"),
    ("Region", "Región", "Region"),
    ("OrganizationAsStored", "Organización tal como se almacena", "Organisation as stored"),
    ("EncodingRepaired", "Codificación reparada", "Encoding repaired"),
    ("StakeholderCategoryAsStored", "Categoría tal como se almacena", "Category as stored"),
    ("QuestionsAnswered", "Preguntas contestadas", "Questions answered"),
    ("ResponseCharacters", "Caracteres de respuesta", "Characters of response"),
]


def pagina_ficha(r):
    filas = ""
    for clave, es, en in ETIQUETAS:
        v = str(r[clave])
        clase = ""
        if clave == "OrganizationAsStored" and r["EncodingRepaired"] == "yes":
            clase = ' class="mono repaired"'
        elif clave in ("ID", "QuestionsAnswered", "ResponseCharacters"):
            clase = ' class="mono"'
        filas += (f"<div><dt>{es}<span>{en}</span></dt>"
                  f"<dd{clase}>{html.escape(v)}</dd></div>")
    cuerpo = f"""
<h1>{html.escape(r["Organization"])}</h1>
<p class="gloss">Registro {r["ID"]} · Record {r["ID"]}</p>
<dl class="record">{filas}</dl>
<h2>El mismo registro en otros sitios</h2>
<p class="note">
<a href="{r['FrenchReplicaRecord']}">Ficha en la réplica de CeSIA</a><br>
<a href="https://www.un.org/global-dialogue-ai-governance/en/inputs">Página oficial de aportaciones</a>
(el corpus se carga dentro de un marco y no tiene dirección por registro)
</p>
"""
    return marco(f'{r["Organization"]} · Anclame', cuerpo, 2,
                 f'Registro {r["ID"]} del Diálogo Global sobre Gobernanza de la IA: '
                 f'{r["Organization"]}, {r["StakeholderCategory"]}, {r["Region"]}.')


def pagina_metodo(proc):
    filas = "".join(
        f"<div><dt>{html.escape(k)}</dt><dd class='mono'>{html.escape(str(v))}</dd></div>"
        for k, v in proc.items() if k != "documento")
    cuerpo = f"""
<h1>Procedencia</h1>
<p class="gloss">How this register was obtained</p>
<p>La página oficial de aportaciones no sirve ni una base de datos ni un fichero de datos.
Carga un marco con una aplicación alojada en otro dominio, y el corpus entero viaja
incrustado como texto dentro de uno de sus ficheros de programa, que el navegador trocea
al vuelo. El nombre de ese fichero cambia cada vez que la aplicación se reconstruye, de
modo que tampoco él tiene una dirección estable.</p>
<p class="en">The official contributions page serves neither a database nor a data file.
It loads a frame holding an application on another domain, and the entire corpus travels
embedded as text inside one of its program files, which the browser splits up on the fly.
The name of that file changes every time the application is rebuilt, so not even it has a
stable address.</p>
<p>Lo que sigue permite a cualquiera repetir la extracción y obtener las mismas huellas.</p>
<dl class="record">{filas}</dl>
"""
    return marco("Procedencia · Anclame", cuerpo, 0)


def pagina_privacidad():
    cuerpo = """
<h1>Privacidad y retirada</h1>
<p class="lead">Este registro contiene, en su mayor parte, nombres de organizaciones.
Una parte menor son nombres de personas que participaron a título individual. Si eres una
de ellas y no quieres aparecer aquí, escribe y se retira.</p>

<h2>Quién responde de esto</h2>
<p>Sara Sanz Herguedas, investigadora independiente.
ORCID <a href="https://orcid.org/0009-0000-7610-6408">0009-0000-7610-6408</a>.
Correo de contacto: <a href="mailto:privacidad@anclame.org">privacidad@anclame.org</a>.</p>

<h2>Qué datos hay</h2>
<p>Por cada aportación: el identificador que le asignó el Diálogo Global, el nombre de la
organización o de la persona tal como ella misma lo escribió, la categoría de participante,
la región, cuántas preguntas contestó y cuántos caracteres ocupan sus respuestas.</p>
<p><strong>No se publica el texto de las respuestas.</strong> No hay direcciones de correo,
ni teléfonos, ni direcciones postales, ni ningún dato que no estuviera ya publicado.</p>

<h2>De dónde salen</h2>
<p>Del corpus que Naciones Unidas publica en la
<a href="https://www.un.org/global-dialogue-ai-governance/en/inputs">página de aportaciones
del Diálogo Global sobre Gobernanza de la IA</a>. Al enviar su aportación, cada participante
dio o no su consentimiento para que se publicara con atribución; solo se publicaron las que
lo dieron. La página de <a href="method.html">Procedencia</a> documenta cómo se obtuvieron
los datos y permite comprobarlo.</p>

<h2>Por qué se publica</h2>
<p>Porque una aportación a una consulta pública que no se puede encontrar ni citar queda,
en la práctica, fuera del registro público. El corpus oficial se sirve dentro de un marco
marcado para que los buscadores no lo indexen, sin dirección propia para cada aportación.
Este registro existe para darles esa dirección.</p>
<p>La base de tratamiento es el interés legítimo previsto en el artículo 6.1.f del
Reglamento General de Protección de Datos: un fin de interés público, sobre datos que sus
titulares consintieron publicar, con el mínimo de información necesaria para cumplirlo.
Puedes solicitar copia del análisis que sustenta esa valoración.</p>

<h2>Cómo pedir que se retire</h2>
<p>Escribe a <a href="mailto:privacidad@anclame.org">privacidad@anclame.org</a> indicando el
identificador o el nombre que aparece. No hace falta motivar la petición ni acreditar nada
más allá de que el registro es tuyo.</p>
<p>La retirada se hace en un plazo máximo de un mes y normalmente en pocos días. Al
retirarse, el nombre, la categoría, la región y los enlaces desaparecen. <strong>El
identificador permanece, con una nota de que el registro fue retirado a petición de su
titular.</strong> Se hace así para que los recuentos del registro sigan siendo exactos: si
los registros desaparecieran sin dejar rastro, el sitio afirmaría un total que no se podría
verificar. Nadie queda identificado por un número que ya era público.</p>
<p>También puedes pedir que se corrija un dato, que se rectifique la codificación de tu
nombre, o una copia de lo que hay sobre ti.</p>

<h2>Lo que este sitio no puede hacer</h2>
<p>Este registro es una copia. Retirar un dato de aquí no lo retira del sitio de Naciones
Unidas ni de la <a href="https://aidialoguereport.org/">réplica publicada por CeSIA</a>.
Para eso hay que dirigirse a la Secretaría Conjunta del Diálogo Global, en
<a href="mailto:aidialogue@un.org">aidialogue@un.org</a>.</p>

<h2>Cookies y analítica</h2>
<p>No hay. Este sitio no instala cookies, no incorpora analítica, no carga tipografías ni
recursos de terceros y no registra quién lo visita. El alojamiento conserva registros
técnicos propios sobre los que quien publica no tiene control.</p>

<h2>Reclamar</h2>
<p>Si consideras que el tratamiento no es correcto, puedes reclamar ante la Agencia Española
de Protección de Datos, <a href="https://www.aepd.es">aepd.es</a>.</p>

<h2>Summary in English</h2>
<p class="en">This register holds metadata about written contributions to the UN Global
Dialogue on AI Governance: identifier, organisation or individual name as given by the
contributor, stakeholder category, region, and the size of the response. It does not hold
the text of the answers. The data comes from the corpus published by the United Nations,
where contributors had consented to publication with attribution. The basis for processing
is legitimate interest under Article 6(1)(f) GDPR. To have your record withdrawn, write to
privacidad@anclame.org quoting the identifier or name; withdrawal takes place within one
month. The identifier remains with a note that the record was withdrawn at its holder's
request, so that the totals stay accurate. Withdrawal here does not remove anything from
the United Nations site or from the CeSIA replica. This site sets no cookies and runs no
analytics.</p>

<p class="small">Última revisión: 24 de septiembre de 2026.</p>
"""
    return marco("Privacidad y retirada · Anclame", cuerpo, 0)


# --------------------------------------------------------------------------
def main():
    fuente = os.path.join(RAIZ, FUENTE)
    if not os.path.exists(fuente):
        sys.exit("Falta el fichero de origen: " + fuente)

    texto = extraer_csv(fuente)
    regs, cols = construir(texto)
    b = open(fuente, "rb").read()

    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "directory.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(regs)

    proc = {
        "documento": "Procedencia",
        "fecha_de_extraccion": "2026-09-23",
        "pagina_oficial": "https://www.un.org/global-dialogue-ai-governance/en/inputs",
        "aplicacion_incrustada": "https://aiwritteninputs.vercel.app/",
        "artefacto_de_origen": SERVIDOR["url"],
        "artefacto_bytes_en_el_servidor": SERVIDOR["bytes"],
        "artefacto_sha256_en_el_servidor": SERVIDOR["sha256"],
        "artefacto_bytes_de_la_copia_local": len(b),
        "artefacto_sha256_de_la_copia_local": hashlib.sha256(b).hexdigest(),
        "nota_sobre_la_copia_local":
            "La copia local difiere del original en 4 bytes: dos apariciones de U+FFFC "
            "fueron convertidas en espacios por la cadena de descarga y subida. La huella "
            "con valor probatorio es la calculada contra el servidor.",
        "csv_metodo_de_extraccion":
            "Se localiza la comilla invertida que abre el literal de plantilla antes de la "
            "cabecera 'ID,Organization,Stakeholder category,Region' y se recorre hasta la "
            "primera comilla invertida sin escapar, aplicando las reglas de escape de "
            "literal de plantilla de ECMAScript. Se descarta la marca de orden de bytes.",
        "csv_caracteres_puntos_de_codigo": len(texto),
        "csv_caracteres_unidades_utf16": len(texto) + sum(1 for c in texto if ord(c) > 0xFFFF),
        "csv_sha256_utf8": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
        "registros": len(regs),
        "identificadores_unicos": len({r["ID"] for r in regs}),
        "registros_declarados_por_el_faq_oficial": 1532,
        "columnas": cols,
        "contenido_omitido_deliberadamente":
            "El texto de las respuestas no se reproduce. Solo metadatos y magnitudes.",
    }
    json.dump(proc, open(os.path.join(DATA, "provenance.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(DOCS)
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    open(os.path.join(DOCS, "style.css"), "w", encoding="utf-8").write(CSS)
    open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(pagina_indice(regs, cols))
    open(os.path.join(DOCS, "register.html"), "w", encoding="utf-8").write(pagina_lista(regs))
    open(os.path.join(DOCS, "method.html"), "w", encoding="utf-8").write(pagina_metodo(proc))
    open(os.path.join(DOCS, "privacy.html"), "w", encoding="utf-8").write(pagina_privacidad())
    for r in regs:
        d = os.path.join(DOCS, "entry", r["ID"])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(pagina_ficha(r))

    print(f"{len(regs)} registros -> data/directory.csv y docs/")


if __name__ == "__main__":
    main()
