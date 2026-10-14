# -*- coding: utf-8 -*-
"""Generación de nubes de palabras por categoría temática."""

import nltk
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from PIL import Image
import ast
# Descargar stopwords de NLTK (solo la primera vez)
nltk.download('stopwords')

from nltk.corpus import stopwords

def normalizar_lista(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return []
    return []

def get_texto(categoria):
  novelas = {'viceversa' : '/content/VIceversa - filtrado experto.xlsx',
  'renacer' : '/content/renacer_intermedio_clasificado.xlsx',
  'asuntos_pendientes': '/content/Asuntos pendientes - filtrado experto.xlsx'}
  texto = ''
  for novela, path in novelas.items():
    df_clasificado = pd.read_excel(path)
    df_clasificado['categorias_detectadas_temp'] = df_clasificado['categorias_detectadas'].apply(normalizar_lista)

    df_clasificado = df_clasificado[df_clasificado['categorias_detectadas_temp'].apply(lambda x: categoria in x)]
    print(f"Total de comentarios categoria {categoria} de novela {novela}: {len(df_clasificado)}")
    texto_temp = ' '.join(df_clasificado['textOriginal'].astype(str))
    texto += texto_temp
    print(f"Longitud de texto {len(texto)}")
  return texto

stop_words = set(stopwords.words('spanish'))

def crear_elipse(ancho=1000, alto=600):
    x, y = np.ogrid[:alto, :ancho]
    mask = ((x - alto/2) / (alto/2)) ** 2 + ((y - ancho/2) / (ancho/2)) ** 2 > 1
    return (255 * mask.astype(int)).astype(np.uint8)

# Obtener stopwords en español
stop_words = set(stopwords.words('spanish'))

# Puedes agregar palabras adicionales
stop_words.update(['Aitana', 'Rebeca', 'Gerardo', 'Silvio', 'Rosa', 'Patricia', 'q', 'Adriana', 'Luis Manuel', 'si'])
mask = crear_elipse()
categorias = ['Maternidad', 'Paternidad', 'Violencia de género']
for categoria in categorias:
  texto = get_texto(categoria)

  nube = WordCloud(width=800, height=800,
                 background_color='white',
                 mask=mask,
                 stopwords=stop_words,
                 contour_color='steelblue').generate(texto)
  nube.to_file(f'nube_{categoria}.png')
  # plt.figure(figsize=(10, 5))
  # plt.imshow(nube, interpolation='bilinear')
  # plt.axis('off')
  # plt.show()

