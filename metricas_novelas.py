# -*- coding: utf-8 -*-
import ast
import pandas as pd

# Configuración de novelas
novelas_config = {
    'asuntospendientes': {
        'total': 'comentarios/asuntospendientes.csv',
        'relevantes': 'Ultimos trabajos/Asuntos pendientes - filtrado experto.xlsx',
        'descartados': 'comentarios_filtrados/asuntospendientes.csv_descartados.csv',
        'clasificado': 'Ultimos trabajos/Asuntos pendientes - filtrado experto.xlsx'
    },
    'renacer': {
        'total': 'comentarios/renacer.csv',
        'relevantes': 'Ultimos trabajos/renacer_intermedio_clasificado.xlsx',
        'descartados': 'comentarios_filtrados/renacer_descartados.csv',
        'clasificado': 'Ultimos trabajos/renacer_intermedio_clasificado.xlsx'
    },
    'viceversa': {
        'total': 'comentarios/viceversa.csv',
        'relevantes': 'Ultimos trabajos/VIceversa - filtrado experto.xlsx',
        'descartados': 'comentarios_filtrados/viceversa.csv_descartados.csv',
        'clasificado': 'Ultimos trabajos/VIceversa - filtrado experto.xlsx'
    }
}

# Función para normalizar listas
def normalizar_lista(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except (ValueError, SyntaxError):
            return []
    return []

# Función para clasificar por longitud
def clasificar_por_longitud(longitud):
    if longitud < 50:
        return 'Muy corto'
    elif longitud < 100:
        return 'Corto'
    elif longitud < 200:
        return 'Medio'
    elif longitud < 400:
        return 'Largo'
    else:
        return 'Muy largo'

# Diccionario para almacenar todas las métricas
resumen_metricas = {}

print("=" * 80)
print("RESUMEN GENERAL DE TODAS LAS MÉTRICAS POR NOVELA")
print("=" * 80)

for novela, paths in novelas_config.items():
    print(f"\n{'=' * 80}")
    print(f"NOVELA: {novela.upper()}")
    print(f"{'=' * 80}")
    
    metricas_novela = {}
    
    # 1. MÉTRICAS DE FILTRADO
    print(f"\n1. MÉTRICAS DE FILTRADO:")
    print("-" * 40)
    df_total = pd.read_csv(paths['total'])
    df_relevantes = pd.read_excel(paths['relevantes'])
    df_descartados = pd.read_csv(paths['descartados'])
    
    total = len(df_total)
    relevantes = len(df_relevantes)
    descartados = total - relevantes
    pct_relevantes = (relevantes / total) * 100
    pct_descartados = (descartados / total) * 100
    
    metricas_novela['total_comentarios'] = total
    metricas_novela['comentarios_relevantes'] = relevantes
    metricas_novela['comentarios_descartados'] = descartados
    metricas_novela['porcentaje_relevantes'] = pct_relevantes
    metricas_novela['porcentaje_descartados'] = pct_descartados
    
    print(f"  • Total de comentarios: {total:,}")
    print(f"  • Comentarios relevantes: {relevantes:,} ({pct_relevantes:.2f}%)")
    print(f"  • Comentarios descartados: {descartados:,} ({pct_descartados:.2f}%)")
    
    # 2. ANÁLISIS DE COMENTARIOS CLASIFICADOS
    print(f"\n2. ANÁLISIS DE POLARIDAD:")
    print("-" * 40)
    df_clasificado = pd.read_excel(paths['clasificado'])
    
    # Filtrar comentarios con categorías vacías
    df_clasificado['categorias_detectadas_temp'] = df_clasificado['categorias_detectadas'].apply(normalizar_lista)
    comentarios_antes = len(df_clasificado)
    df_clasificado = df_clasificado[df_clasificado['categorias_detectadas_temp'].apply(lambda x: len(x) > 0)]
    comentarios_despues = len(df_clasificado)
    comentarios_sin_categoria = comentarios_antes - comentarios_despues
    
    print(f"  • Comentarios sin categorías descartados: {comentarios_sin_categoria:,}")
    print(f"  • Comentarios con categorías: {comentarios_despues:,}")
    
    metricas_novela['comentarios_sin_categoria'] = comentarios_sin_categoria
    metricas_novela['comentarios_con_categoria'] = comentarios_despues
    
    polaridad_dist = df_clasificado['polaridad'].value_counts(normalize=True) * 100
    metricas_novela['polaridad'] = polaridad_dist.to_dict()
    
    for polaridad, pct in polaridad_dist.items():
        print(f"  • {polaridad}: {pct:.2f}%")
    
    # 3. ANÁLISIS DE INTENSIDAD
    print(f"\n3. ANÁLISIS DE INTENSIDAD:")
    print("-" * 40)
    intensidad_promedio = df_clasificado['intensidad'].mean()
    intensidad_mediana = df_clasificado['intensidad'].median()
    intensidad_std = df_clasificado['intensidad'].std()
    
    metricas_novela['intensidad_promedio'] = intensidad_promedio
    metricas_novela['intensidad_mediana'] = intensidad_mediana
    metricas_novela['intensidad_std'] = intensidad_std
    
    print(f"  • Promedio: {intensidad_promedio:.2f}")
    print(f"  • Mediana: {intensidad_mediana:.2f}")
    print(f"  • Desviación estándar: {intensidad_std:.2f}")
    
    # Distribución (opcional, para referencia)
    intensidad_dist = df_clasificado['intensidad'].value_counts(normalize=True) * 100
    print(f"\n  Distribución:")
    for intensidad, pct in intensidad_dist.items():
        print(f"    • {intensidad}: {pct:.2f}%")
    
    # 4. ANÁLISIS DE LEGITIMACIÓN
    print(f"\n4. ANÁLISIS DE LEGITIMACIÓN:")
    print("-" * 40)
    
    # Agrupar legitimación de forma inteligente
    def agrupar_legitimacion(valor):
        valor_str = str(valor).strip()
        
        # Si ya es exactamente uno de los valores principales, mantenerlo
        if valor_str in ['Rechazo', 'Aceptación', 'Neutra']:
            return valor_str
        
        # Convertir a minúsculas para búsqueda
        valor_lower = valor_str.lower()
        
        # Verificar si contiene las palabras clave
        tiene_rechazo = 'rechazo' in valor_lower
        tiene_aceptacion = 'aceptación' in valor_lower or 'aceptacion' in valor_lower
        
        # Clasificar según el contenido
        if tiene_rechazo and tiene_aceptacion:
            return 'Mixta'
        elif tiene_rechazo:
            return 'Rechazo'
        elif tiene_aceptacion:
            return 'Aceptación'
        else:
            return 'Neutra'
    
    df_clasificado['legitimacion_agrupada'] = df_clasificado['legitimacion'].apply(agrupar_legitimacion)
    legitimacion_dist = df_clasificado['legitimacion_agrupada'].value_counts(normalize=True) * 100
    metricas_novela['legitimacion'] = legitimacion_dist.to_dict()
    
    for legitimacion, pct in legitimacion_dist.items():
        print(f"  • {legitimacion}: {pct:.2f}%")
    
    # 5. CATEGORÍAS DETECTADAS
    print(f"\n5. TOP 10 CATEGORÍAS MÁS FRECUENTES:")
    print("-" * 40)
    df_clasificado['categorias_detectadas_func'] = df_clasificado['categorias_detectadas'].apply(normalizar_lista)
    df_exploded = df_clasificado.explode('categorias_detectadas_func')
    categorias_dist = df_exploded['categorias_detectadas_func'].value_counts(normalize=True) * 100
    metricas_novela['categorias'] = categorias_dist.to_dict()
    
    for categoria, pct in categorias_dist.head(10).items():
        print(f"  • {categoria}: {pct:.2f}%")
    
    # 6. ANÁLISIS DE LONGITUD DE COMENTARIOS
    print(f"\n6. ANÁLISIS DE LONGITUD DE COMENTARIOS:")
    print("-" * 40)
    df_clasificado['cantidad_caracteres'] = df_clasificado['textOriginal'].str.len()
    df_clasificado['clasificacion_longitud'] = df_clasificado['cantidad_caracteres'].apply(clasificar_por_longitud)
    
    print(f"  Estadísticas descriptivas:")
    stats = df_clasificado['cantidad_caracteres'].describe()
    print(f"    - Media: {stats['mean']:.2f} caracteres")
    print(f"    - Mediana: {stats['50%']:.2f} caracteres")
    print(f"    - Desviación estándar: {stats['std']:.2f}")
    print(f"    - Mínimo: {stats['min']:.0f} caracteres")
    print(f"    - Máximo: {stats['max']:.0f} caracteres")
    
    metricas_novela['longitud_media'] = stats['mean']
    metricas_novela['longitud_mediana'] = stats['50%']
    metricas_novela['longitud_std'] = stats['std']
    metricas_novela['longitud_min'] = stats['min']
    metricas_novela['longitud_max'] = stats['max']
    
    print(f"\n  Distribución por clasificación:")
    longitud_dist = df_clasificado['clasificacion_longitud'].value_counts(normalize=True) * 100
    metricas_novela['clasificacion_longitud'] = longitud_dist.to_dict()
    
    for clasificacion, pct in longitud_dist.items():
        print(f"    • {clasificacion}: {pct:.2f}%")
    
    resumen_metricas[novela] = metricas_novela

# RESUMEN COMPARATIVO ENTRE NOVELAS
print(f"\n\n{'=' * 80}")
print("RESUMEN COMPARATIVO ENTRE NOVELAS")
print(f"{'=' * 80}")

# Crear DataFrame comparativo
comparativo_data = []
for novela, metricas in resumen_metricas.items():
    row = {
        'Novela': novela.upper(),
        'Total Comentarios': metricas['total_comentarios'],
        'Comentarios Relevantes': metricas['comentarios_relevantes'],
        '% Relevantes': f"{metricas['porcentaje_relevantes']:.2f}%",
        'Longitud Media': f"{metricas['longitud_media']:.0f}",
        'Longitud Mediana': f"{metricas['longitud_mediana']:.0f}"
    }
    comparativo_data.append(row)

df_comparativo = pd.DataFrame(comparativo_data)
print("\n")
print(df_comparativo.to_string(index=False))

print(f"\n{'=' * 80}")
print("Análisis completado exitosamente")
print(f"{'=' * 80}")

# Exportar a fichero texto con formato específico
for novela, metricas in resumen_metricas.items():
    with open(f"resumen_metricas_{novela}.txt", "w", encoding='utf-8') as f:
        f.write(f"{'=' * 80}\n")
        f.write(f"RESUMEN DE MÉTRICAS - NOVELA: {novela.upper()}\n")
        f.write(f"{'=' * 80}\n\n")
        
        # 1. Métricas de Filtrado
        f.write("1. MÉTRICAS DE FILTRADO:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  • Total de comentarios: {metricas['total_comentarios']:,}\n")
        f.write(f"  • Comentarios relevantes: {metricas['comentarios_relevantes']:,} ({metricas['porcentaje_relevantes']:.2f}%)\n")
        f.write(f"  • Comentarios descartados: {metricas['comentarios_descartados']:,} ({metricas['porcentaje_descartados']:.2f}%)\n\n")
        
        # 2. Análisis de Polaridad
        f.write("2. ANÁLISIS DE POLARIDAD:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  • Comentarios sin categorías descartados: {metricas['comentarios_sin_categoria']:,}\n")
        f.write(f"  • Comentarios con categorías: {metricas['comentarios_con_categoria']:,}\n\n")
        f.write("  Distribución de polaridad:\n")
        for polaridad, pct in metricas['polaridad'].items():
            f.write(f"    • {polaridad}: {pct:.2f}%\n")
        f.write("\n")
        
        # 3. Análisis de Intensidad
        f.write("3. ANÁLISIS DE INTENSIDAD:\n")
        f.write("-" * 40 + "\n")
        f.write(f"  • Promedio: {metricas['intensidad_promedio']:.2f}\n")
        f.write(f"  • Mediana: {metricas['intensidad_mediana']:.2f}\n")
        f.write(f"  • Desviación estándar: {metricas['intensidad_std']:.2f}\n\n")
        
        # 4. Análisis de Legitimación
        f.write("4. ANÁLISIS DE LEGITIMACIÓN:\n")
        f.write("-" * 40 + "\n")
        for legitimacion, pct in metricas['legitimacion'].items():
            f.write(f"  • {legitimacion}: {pct:.2f}%\n")
        f.write("\n")
        
        # 5. Top 10 Categorías
        f.write("5. TOP 10 CATEGORÍAS MÁS FRECUENTES:\n")
        f.write("-" * 40 + "\n")
        categorias_ordenadas = sorted(metricas['categorias'].items(), key=lambda x: x[1], reverse=True)[:10]
        for categoria, pct in categorias_ordenadas:
            f.write(f"  • {categoria}: {pct:.2f}%\n")
        f.write("\n")
        
        # 6. Análisis de Longitud
        f.write("6. ANÁLISIS DE LONGITUD DE COMENTARIOS:\n")
        f.write("-" * 40 + "\n")
        f.write("  Estadísticas descriptivas:\n")
        f.write(f"    - Media: {metricas['longitud_media']:.2f} caracteres\n")
        f.write(f"    - Mediana: {metricas['longitud_mediana']:.2f} caracteres\n")
        f.write(f"    - Desviación estándar: {metricas['longitud_std']:.2f}\n")
        f.write(f"    - Mínimo: {metricas['longitud_min']:.0f} caracteres\n")
        f.write(f"    - Máximo: {metricas['longitud_max']:.0f} caracteres\n\n")
        f.write("  Distribución por clasificación:\n")
        for clasificacion, pct in metricas['clasificacion_longitud'].items():
            f.write(f"    • {clasificacion}: {pct:.2f}%\n")
        f.write("\n")
        
        f.write(f"{'=' * 80}\n")
        f.write("Análisis completado exitosamente\n")
        f.write(f"{'=' * 80}\n")