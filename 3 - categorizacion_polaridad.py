# -*- coding: utf-8 -*-
"""Categorización temática y resumen de comentarios con Gemini.

Clasifica los comentarios en las categorías de cultura reproductiva
definidas y genera un resumen cualitativo por categoría.
"""

import google.generativeai as genai
import pandas as pd
import json
import time
from tqdm import tqdm
import os

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
API_KEY = ""
ARCHIVO_ENTRADA = '' # Tu archivo limpio
ARCHIVO_RESULTADOS = ''

# Tus categorías exactas
CATEGORIAS_DEFINIDAS = [
    "Embarazos",
    "Cantidad de hijos",
    "Divorcios",
    "Uso de métodos anticonceptivos",
    "Aborto",
    "Relaciones sexuales",
    "Maternidad",
    "Paternidad",
    "Violencia de género"
]

genai.configure(api_key=API_KEY)

# Configuración del modelo (Usamos Flash para velocidad y capacidad de contexto)
generation_config = {"temperature": 0.2, "response_mime_type": "application/json"}
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash", # O usa "gemini-flash-latest"
    generation_config=generation_config,
    safety_settings=safety_settings
)

# ==========================================
# 2. FUNCIONES DE PROMPT
# ==========================================

def clasificar_lote(lote_datos):
    """Clasifica una lista de comentarios en las categorías definidas."""
    json_text = json.dumps(lote_datos, ensure_ascii=False)
    categorias_str = ", ".join(CATEGORIAS_DEFINIDAS)

    prompt = f"""
    Actúa como sociólogo. Clasifica los siguientes comentarios según si tocan alguno de estos temas:
    LISTA DE TEMAS: [{categorias_str}]

    INPUT (JSON):
    {json_text}

    INSTRUCCIONES:
    - Devuelve un JSON Array con el mismo "id".
    - En "categorias_detectadas" pon una lista con los temas exactos que apliquen.
    - Si no aplica ninguno, deja la lista vacía [].
    - Un comentario puede tener varias categorías (ej: Divorcio y Paternidad).

    OUTPUT ESPERADO:
    [
      {{"id": 1, "categorias_detectadas": ["Divorcios", "Paternidad"]}},
      ...
    ]
    """
    return prompt

def generar_resumen_tematico(categoria, lista_comentarios):
    """Genera un resumen cualitativo de un grupo de comentarios."""
    # Unimos los comentarios en un solo texto gigante
    texto_consolidado = "\n- ".join([c[:500] for c in lista_comentarios]) # Recortamos un poco por seguridad

    prompt = f"""
    Actúa como investigador social. He recopilado {len(lista_comentarios)} comentarios de una telenovela cubana que tratan sobre: "{categoria}".

    Tu tarea es generar un RESUMEN EJECUTIVO de lo que dice la audiencia sobre este tema.

    COMENTARIOS A ANALIZAR:
    {texto_consolidado}

    Genera un JSON con esta estructura:
    {{
      "categoria": "{categoria}",
      "cantidad_menciones": {len(lista_comentarios)},
      "sentimiento_predominante": "Positivo/Negativo/Ambivalente",
      "ideas_principales": ["Idea 1", "Idea 2", "Idea 3"],
      "resumen_narrativo": "Un párrafo denso (aprox 100 palabras) explicando la postura sociológica de la audiencia sobre este tema, citando tensiones o consensos."
    }}
    """
    return prompt

# ==========================================
# 3. PROCESO PRINCIPAL
# ==========================================

def ejecutar_analisis():
    # --- PASO A: CARGAR Y CLASIFICAR ---
    print("--- PASO 1: CLASIFICACIÓN DE COMENTARIOS ---")
    df = pd.read_excel(ARCHIVO_ENTRADA)
    if 'id_unico' not in df.columns: df['id_unico'] = df.index

    # Preparamos lotes de 20 para clasificar
    TAMANO_LOTE = 20
    resultados_clasificacion = []

    for i in tqdm(range(0, len(df), TAMANO_LOTE)):
        chunk = df.iloc[i : i + TAMANO_LOTE]
        lote_api = [{"id": int(r['id_unico']), "texto": str(r['textOriginal'])[:400]} for _, r in chunk.iterrows()]

        try:
            response = model.generate_content(clasificar_lote(lote_api))
            data = json.loads(response.text)

            # Manejo de errores si la IA devuelve diccionario en vez de lista
            if isinstance(data, dict): data = data.get('resultados', [])

            resultados_clasificacion.extend(data)
            time.sleep(2) # Pausa leve

        except Exception as e:
            print(f"Error en lote {i}: {e}")
            time.sleep(5)

    # Convertimos resultados a DataFrame y unimos
    df_res = pd.DataFrame(resultados_clasificacion)
    # Explotamos las listas: si un comentario tiene 2 temas, creamos 2 filas para facilitar el agrupamiento
    df_final = pd.merge(df, df_res, left_on='id_unico', right_on='id', how='left')

    # Guardamos la clasificación cruda por si acaso
    df_final.to_excel("viceversa_intermedio_clasificado.xlsx", index=False)

    # --- PASO B: AGRUPAR Y RESUMIR ---
    print("\n--- PASO 2: GENERACIÓN DE RESÚMENES POR CATEGORÍA ---")

    # Explotar la columna de listas para poder filtrar fácilmente
    # Primero aseguramos que sea lista real (a veces al cargar de excel se vuelve string)
    def normalizar_lista(x):
        if isinstance(x, list): return x
        return []

    df_final['categorias_detectadas'] = df_final['categorias_detectadas'].apply(normalizar_lista)
    df_exploded = df_final.explode('categorias_detectadas')

    informes_por_categoria = []

    for cat in CATEGORIAS_DEFINIDAS:
        # Filtramos todos los comentarios de esa categoría
        subset = df_exploded[df_exploded['categorias_detectadas'] == cat]
        comentarios_txt = subset['textOriginal'].dropna().tolist()

        cantidad = len(comentarios_txt)
        print(f"Procesando '{cat}': {cantidad} comentarios encontrados.")

        if cantidad > 0:
            try:
                # Si son demasiados (>500), tomamos una muestra para el resumen para no saturar
                # (Aunque Gemini 2.5 aguanta mucho contexto, esto es por seguridad y velocidad)
                muestra = comentarios_txt if cantidad < 500 else comentarios_txt[:500]

                prompt_resumen = generar_resumen_tematico(cat, muestra)
                response = model.generate_content(prompt_resumen)
                analisis_cat = json.loads(response.text)
                informes_por_categoria.append(analisis_cat)

                time.sleep(4)
            except Exception as e:
                print(f"Error resumiendo {cat}: {e}")
        else:
            informes_por_categoria.append({
                "categoria": cat,
                "cantidad_menciones": 0,
                "resumen_narrativo": "No se encontraron comentarios suficientes."
            })

    # --- PASO C: GUARDAR REPORTE FINAL ---
    df_reporte = pd.DataFrame(informes_por_categoria)

    # Guardar resumenes
    df_reporte.to_excel(ARCHIVO_RESULTADOS, index=False)
    print(f"\n¡PROCESO TERMINADO! Abre el archivo '{ARCHIVO_RESULTADOS}' para ver los resúmenes.")

ejecutar_analisis()