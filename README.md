# Anclame

Registro citable de las aportaciones escritas al Diálogo Global sobre Gobernanza de la
Inteligencia Artificial de Naciones Unidas.

*A citable register of the written contributions to the UN Global Dialogue on AI
Governance.*

---

## Qué es

El Diálogo Global publica las aportaciones de la ciudadanía y de las organizaciones que
respondieron a su convocatoria. Las publica dentro de un marco alojado en otro dominio,
marcado para que los buscadores no lo indexen, sin dirección propia para cada aportación
y sin fichero de datos. Una aportación publicada así no se puede citar, no se puede
enlazar y no se puede encontrar.

Este repositorio le da a cada aportación una dirección estable, de la forma
`/entry/669/`, y publica los metadatos en un fichero abierto con su procedencia
documentada.

**Aquí hay metadatos. No hay texto de las respuestas**, y no lo habrá sin el
consentimiento de quien lo escribió.

## What this is

The Global Dialogue publishes the contributions sent by citizens and organisations that
answered its call. It publishes them inside a frame hosted on another domain, marked so
that search engines will not index it, with no address of its own for each contribution
and no data file. A contribution published this way cannot be cited, linked or found.

This repository gives each contribution a stable address, in the form `/entry/669/`, and
publishes the metadata as an open file with documented provenance.

**This holds metadata. It does not hold the text of the answers**, and will not without
the consent of whoever wrote them.

---

## Contenido · Contents

| Ruta | Qué es |
| --- | --- |
| `data/directory.csv` | Los 1.534 registros con sus metadatos. Cabeceras en inglés. |
| `data/provenance.json` | De dónde sale el fichero, cómo se extrajo y sus huellas SHA-256. |
| `build.py` | Reconstruye los datos y el sitio a partir del artefacto de origen. |
| `docs/` | El sitio publicado. |

### Columnas de `directory.csv`

| Columna | Qué contiene |
| --- | --- |
| `ID` | Identificador tal como lo asigna el origen. |
| `Organization` | Nombre con la codificación reparada cuando estaba dañada. |
| `StakeholderCategory` | Categoría normalizada. |
| `Region` | Región, tal como está en el origen. |
| `OrganizationAsStored` | Nombre tal como está almacenado, sin tocar. |
| `EncodingRepaired` | `yes` si la reparación cambió algo. |
| `StakeholderCategoryAsStored` | Categoría tal como está almacenada, con sus espacios. |
| `QuestionsAnswered` | Cuántas de las once preguntas tienen respuesta. |
| `ResponseCharacters` | Longitud total de las respuestas, en caracteres. |
| `FrenchReplicaRecord` | La misma aportación en la réplica de CeSIA. |

Las dos últimas columnas describen el tamaño de la aportación sin reproducir nada de su
contenido.

---

## Lo que se encontró · What was found

**1.534 registros frente a 1.532 declarados.** El FAQ oficial dice 1.532. El fichero
tiene 1.534, con 1.534 identificadores distintos y ninguno repetido. La diferencia no
está explicada.

**22 nombres de organización con la codificación dañada**, por doble codificación UTF-8.
Son 61 registros si se cuentan también las respuestas. Entre ellos, el 669, que aparece
como `Sara Sanz Research Â· AI Behaviour Auditing`.

**Categorías sin normalizar.** Hay 43 registros de sociedad civil, 6 de academia y 5 de
sector privado con espacios finales, más una `International Organization` frente a 145
`International Organisation`. Los filtros del visor oficial no los alcanzan.

**Sin dirección por registro y sin indexar.** El corpus vive en un marco que declara
`noindex, nofollow`. La réplica francesa de CeSIA sí da dirección a cada registro, lo que
demuestra que hacerlo era trivial.

---

## Reproducirlo · Reproducing this

1. Abrir `https://aiwritteninputs.vercel.app/` y localizar en las peticiones de red el
   fichero `QuestionnaireViewer-*.js`. El nombre cambia en cada reconstrucción.
2. Descargarlo y colocarlo en la raíz de este repositorio.
3. Ejecutar `python3 build.py`.

`data/provenance.json` describe el método de extracción con detalle suficiente para
obtener las mismas huellas. Si el artefacto ha cambiado, las huellas no coincidirán: eso
es información, no un error.

---

## Licencia · Licence

El código, bajo licencia MIT. Los metadatos de `data/`, bajo CC0: son hechos sobre
documentos públicos y no se reclama derecho alguno sobre ellos.

## Declaración · Disclosure

Parte afectada: la autora es contribuyente escrita al Diálogo Global, registro 669. Esta
circunstancia se declara porque afecta a la lectura del trabajo, no porque invalide las
comprobaciones, que cualquiera puede repetir.

*Disclosure: the author is a written contributor to the Global Dialogue, record 669. This
is stated because it bears on how the work should be read, not because it undermines the
checks, which anyone can repeat.*

---

<sub>Sara Sanz Herguedas · ORCID [0009-0000-7610-6408](https://orcid.org/0009-0000-7610-6408) · sasanher@bbaa.upv.es</sub>
