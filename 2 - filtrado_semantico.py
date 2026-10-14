# -*- coding: utf-8 -*-
"""Filtrado semántico de comentarios mediante embeddings multilingües.

Selecciona los comentarios relacionados con la cultura reproductiva
comparándolos por similitud coseno con un conjunto de temas objetivo.
"""

import pandas as pd
from sentence_transformers import SentenceTransformer, util

# -----------------------------------------------------------------------------
# 2. CONFIGURACIÓN DEL MODELO SEMÁNTICO
# -----------------------------------------------------------------------------
print("Cargando modelo de IA (esto puede tardar la primera vez)...")
# Usamos un modelo multilingüe optimizado para frases
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 3. DEFINICIÓN DE TUS TEMAS DE INTERÉS
# Aquí describimos semánticamente qué estamos buscando.
# No son palabras clave, son FRASES que definen el concepto.
temas_objetivo = [
    "Discusiones sobre el embarazo, el aborto, métodos anticonceptivos o fertilidad.",
    "Opiniones sobre la crianza de los hijos, la maternidad y la paternidad.",
    "Dinámicas familiares, relaciones entre padres e hijos, abuelos o familia extendida.",
    "Roles de género, machismo, violencia doméstica o comportamiento sexual.",
    "Relaciones de pareja, infidelidad, matrimonio y divorcio."
]

# Creamos un único vector "maestro" que combine estos intereses
# O podemos comparar contra cada uno. Para filtrar, comparar contra todos es mejor.
embeddings_temas = model.encode(temas_objetivo, convert_to_tensor=True)

def analisis(df, output_name):
  # -----------------------------------------------------------------------------
  # 4. PROCESAMIENTO DE COMENTARIOS
  # -----------------------------------------------------------------------------
  print(f"Analizando semánticamente {len(df)} comentarios...")

  # Convertimos todos los comentarios a vectores (embeddings)
  # batch_size=32 procesa de 32 en 32 para no saturar la memoria
  comentarios_lista = df[columna_texto].astype(str).tolist()
  embeddings_comentarios = model.encode(comentarios_lista, batch_size=64, convert_to_tensor=True, show_progress_bar=True)
  # -----------------------------------------------------------------------------
  # 5. CÁLCULO DE SIMILITUD
  # -----------------------------------------------------------------------------

  # Calculamos la similitud coseno entre cada comentario y tus temas
  # Esto nos dará una matriz de puntajes. Nos quedamos con el puntaje más alto
  # de coincidencia con CUALQUIERA de tus temas.
  cosine_scores = util.cos_sim(embeddings_comentarios, embeddings_temas)

  # Obtenemos el score máximo para cada comentario (su mejor coincidencia con tus temas)
  # El resultado es un tensor, lo pasamos a lista.
  max_scores = cosine_scores.max(axis=1).values.cpu().tolist()

  # Agregamos el score al DataFrame
  df['score_relevancia'] = max_scores

  # -----------------------------------------------------------------------------
  # 6. FILTRADO INTELIGENTE
  # -----------------------------------------------------------------------------

  # DEFINIR UMBRAL (THRESHOLD)
  # Los scores van de 0 a 1.
  # Generalmente > 0.25 o 0.30 empieza a ser relevante semánticamente.
  # < 0.20 suele ser ruido o temas muy alejados.
  umbral = 0.28

  df_relevante = df[df['score_relevancia'] >= umbral].copy()
  df_irrelevante = df[df['score_relevancia'] < umbral].copy()

  # Ordenamos los relevantes por score (los más claros primero)
  df_relevante = df_relevante.sort_values(by='score_relevancia', ascending=False)
  # -----------------------------------------------------------------------------
  # 7. EXPORTACIÓN
  # -----------------------------------------------------------------------------
  print("-" * 30)
  print(f"Total procesado: {len(df)}")
  print(f"Relevantes encontrados (Score > {umbral}): {len(df_relevante)}")
  print(f"Descartados: {len(df_irrelevante)}")

  # Guardamos
  df_relevante.to_csv(f"{output_name}_relevantes.csv", index=False)
  df_irrelevante.to_csv(f"{output_name}_descartados.csv", index=False)

  df_minimal = df_relevante[['textOriginal', 'videoId']]
  df_minimal.to_csv(f"{output_name}_minimal_relevantes.csv", index=False)

# 1. CARGAR DATOS
lista = ['/content/renacer.csv', '/content/sabadosgloria.csv', '/content/viceversa.csv', '/content/asuntospendientes.csv']
output_name = ['renacer', 'sabadosgloria.csv', 'viceversa.csv', 'asuntospendientes.csv']
columna_texto = 'textOriginal'

for i,item in enumerate(lista):
  print(f"Comenzando analisis de {output_name[i]}")
  df = pd.read_csv(item)

  print(f"Total de comentarios inicial: {len(df)}")

  # Limpieza básica previa (eliminar vacíos y duplicados)
  df = df.dropna(subset=[columna_texto])
  df = df.drop_duplicates(subset=[columna_texto])

  print(f"Total de comentarios luego de primer filtro: {len(df)}")
  analisis(df, output_name[i])