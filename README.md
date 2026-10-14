# Comunicación y cultura reproductiva en Cuba — código de análisis

Scripts utilizados en la tesis doctoral **"Comunicación y cultura reproductiva en Cuba. Un análisis desde el consumo cultural de telenovelas"** (Universidad de Málaga), de **Lisset Bourzac Macia** ([ORCID 0000-0002-5453-5807](https://orcid.org/0000-0002-5453-5807)).

El código extrae los comentarios publicados en YouTube sobre telenovelas cubanas (*Renacer*, *Viceversa*, *Asuntos pendientes* y el programa *Sábados de Gloria*), selecciona los que tratan temas de cultura reproductiva, los clasifica por categoría temática y calcula métricas descriptivas y nubes de palabras.

## Cómo citar

Si utiliza este código, cite el depósito (ver también `CITATION.cff`):

> Bourzac Macia, L. (2026). *Código de análisis para "Comunicación y cultura reproductiva en Cuba. Un análisis desde el consumo cultural de telenovelas"* (Versión 1.0.0) [Software]. Zenodo. https://doi.org/10.5281/zenodo.XXXXXXX

## Flujo de trabajo

| Paso | Script | Entrada | Salida |
|---|---|---|---|
| 1 | `1 - extraccion_datos.py` | Ficheros `videos<Novela>.txt` con una URL o ID de vídeo por línea | Un CSV de comentarios por vídeo en `comentarios/<Novela>/` y `estadisticas_videos.csv` |
| 2 | `2 - filtrado_semantico.py` | Un CSV de comentarios por novela (columna `textOriginal`) | `<novela>_relevantes.csv`, `<novela>_descartados.csv`, `<novela>_minimal_relevantes.csv` |
| 3 | `3 - categorizacion_polaridad.py` | Excel con los comentarios relevantes | Excel con la clasificación por categoría (`*_intermedio_clasificado.xlsx`) y Excel de resúmenes por categoría |
| — | *Revisión experta* | Clasificación del paso 3 | Ficheros `* - filtrado experto.xlsx` con las columnas `polaridad`, `intensidad` y `legitimacion` |
| 4 | `metricas_novelas.py` | Salidas de los pasos 1–3 y de la revisión experta | `resumen_metricas_<novela>.txt` |
| 5 | `nube_de_palabras.py` | Ficheros clasificados | `nube_<categoria>.png` |

### Metodología

La descripción completa del método se encuentra en la tesis doctoral: el corpus y el periodo de extracción de los datos, los criterios del filtrado semántico, el proceso de categorización, la revisión experta y la codificación de polaridad, intensidad y legitimación.

Los resultados de un modelo de lenguaje (paso 3) no son deterministas, por lo que una nueva ejecución puede producir clasificaciones ligeramente distintas de las recogidas en la tesis.

## Instalación

Requiere Python 3.10 o superior.

```bash
pip install -r requirements.txt
```

## Uso

```bash
# Paso 1: necesita una clave de la API YouTube Data v3
python "1 - extraccion_datos.py" --api-key TU_CLAVE

# Pasos 2 a 5
python "2 - filtrado_semantico.py"
python "3 - categorizacion_polaridad.py"
python metricas_novelas.py
python nube_de_palabras.py
```

Las rutas de entrada y salida están escritas al principio de cada script y deben ajustarse a la estructura local de ficheros. Los scripts 2, 3 y 5 se ejecutaron originalmente en Google Colab (rutas `/content/...`).

Para el script 3 debe asignar una clave de la API de Gemini a la variable `API_KEY`, y las rutas a `ARCHIVO_ENTRADA` y `ARCHIVO_RESULTADOS`. **No publique nunca el script con la clave rellenada.**

## Datos

Este depósito contiene solo el código. Los comentarios descargados no se incluyen, porque contienen datos personales de los usuarios (nombre, canal e imagen de perfil) y porque las condiciones de servicio de la API de YouTube limitan su redistribución. Los datos pueden volver a obtenerse ejecutando el paso 1 con la lista de vídeos analizados, aunque los comentarios eliminados después de la extracción ya no estarán disponibles.

## Licencia

El código se distribuye bajo la licencia MIT (ver `LICENSE`).
