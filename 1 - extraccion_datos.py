import os
import csv
import time
import argparse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def get_video_info(youtube, video_id):
    """
    Obtiene información completa de un video específico de YouTube.
    Retorna un diccionario con título y estadísticas del video.
    """
    try:
        # Solicitar información del video (snippet y statistics)
        video_response = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=video_id
        ).execute()
        
        # Verificar si hay resultados
        if video_response['items']:
            video_data = video_response['items'][0]
            snippet = video_data['snippet']
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            return {
                'title': snippet.get('title', 'Titulo no disponible'),
                'publishedAt': snippet.get('publishedAt', ''),
                'channelTitle': snippet.get('channelTitle', ''),
                'categoryId': snippet.get('categoryId', ''),
                'duration': content_details.get('duration', ''),
                'viewCount': int(statistics.get('viewCount', 0)),
                'likeCount': int(statistics.get('likeCount', 0)),
                'commentCount': int(statistics.get('commentCount', 0))
            }
        else:
            return {
                'title': 'Titulo no disponible',
                'publishedAt': '',
                'channelTitle': '',
                'categoryId': '',
                'duration': '',
                'viewCount': 0,
                'likeCount': 0,
                'commentCount': 0
            }
            
    except HttpError as e:
        print(f"Error al obtener información del video {video_id}: {e}")
        return {
            'title': 'Error al obtener titulo',
            'publishedAt': '',
            'channelTitle': '',
            'categoryId': '',
            'duration': '',
            'viewCount': 0,
            'likeCount': 0,
            'commentCount': 0
        }

def get_video_comments(youtube, video_id, video_info, max_results=100):
    """
    Obtiene los comentarios de un video especifico de YouTube.
    Retorna una lista de diccionarios con los comentarios y sus respuestas.
    """
    comments = []
    
    try:
        # Obtener los comentarios del video
        results = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            textFormat="plainText",
            maxResults=max_results
        ).execute()
        
        # Procesar los resultados
        while results:
            for item in results["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comment_id = item["snippet"]["topLevelComment"]["id"]
                total_reply_count = item["snippet"]["totalReplyCount"]
                
                # Obtener informacion del comentario principal
                comments.append({
                    'videoId': video_id,
                    'videoTitle': video_info['title'],
                    'videoPublishedAt': video_info['publishedAt'],
                    'videoChannelTitle': video_info['channelTitle'],
                    'videoDuration': video_info['duration'],
                    'videoViewCount': video_info['viewCount'],
                    'videoLikeCount': video_info['likeCount'],
                    'videoCommentCount': video_info['commentCount'],
                    'commentId': comment_id,
                    'parentCommentId': '',  # Vacío para comentarios principales
                    'isReply': False,
                    'authorDisplayName': comment["authorDisplayName"],
                    'authorProfileImageUrl': comment["authorProfileImageUrl"],
                    'authorChannelUrl': comment["authorChannelUrl"],
                    'textDisplay': comment["textDisplay"],
                    'textOriginal': comment["textOriginal"],
                    'commentLikeCount': comment["likeCount"],
                    'replyCount': total_reply_count,
                    'commentPublishedAt': comment["publishedAt"],
                    'commentUpdatedAt': comment["updatedAt"]
                })
                
                # Procesar las respuestas si existen
                if "replies" in item:
                    for reply_item in item["replies"]["comments"]:
                        reply = reply_item["snippet"]
                        reply_id = reply_item["id"]
                        
                        comments.append({
                            'videoId': video_id,
                            'videoTitle': video_info['title'],
                            'videoPublishedAt': video_info['publishedAt'],
                            'videoChannelTitle': video_info['channelTitle'],
                            'videoDuration': video_info['duration'],
                            'videoViewCount': video_info['viewCount'],
                            'videoLikeCount': video_info['likeCount'],
                            'videoCommentCount': video_info['commentCount'],
                            'commentId': reply_id,
                            'parentCommentId': comment_id,
                            'isReply': True,
                            'authorDisplayName': reply["authorDisplayName"],
                            'authorProfileImageUrl': reply["authorProfileImageUrl"],
                            'authorChannelUrl': reply["authorChannelUrl"],
                            'textDisplay': reply["textDisplay"],
                            'textOriginal': reply["textOriginal"],
                            'commentLikeCount': reply["likeCount"],
                            'replyCount': 0,  # Las respuestas no tienen respuestas
                            'commentPublishedAt': reply["publishedAt"],
                            'commentUpdatedAt': reply["updatedAt"]
                        })
            
            # Verificar si hay mas comentarios
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=max_results,
                    pageToken=results["nextPageToken"]
                ).execute()
            else:
                break
                
    except HttpError as e:
        print(f"Error al obtener comentarios del video {video_id}: {e}")
    
    return comments

def extract_video_id(url):
    """
    Extrae el ID del video de una URL de YouTube.
    """
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "youtube.com/watch" in url:
        import urllib.parse as urlparse
        parsed_url = urlparse.urlparse(url)
        return urlparse.parse_qs(parsed_url.query)['v'][0]
    else:
        return url  # Asume que ya es un ID

def save_comments_to_csv(video_id, comments, video_title, output_dir):
    """
    Guarda los comentarios y respuestas en un archivo CSV.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = os.path.join(output_dir, f"{video_title}_comments.csv")
    
    if not comments:
        print(f"No se encontraron comentarios para el video {video_id}")
        return
    
    # Contar comentarios y respuestas
    main_comments = sum(1 for c in comments if not c['isReply'])
    replies = sum(1 for c in comments if c['isReply'])
        
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = comments[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for comment in comments:
            writer.writerow(comment)
            
    print(f"Se guardaron {main_comments} comentarios y {replies} respuestas para el video {video_id} en {filename}")
    print(f"Total de interacciones guardadas: {len(comments)}")

def save_video_stats_to_csv(video_stats_list, output_file):
    """
    Guarda las estadísticas generales de todos los videos en un CSV.
    """
    if not video_stats_list:
        print("No hay estadísticas de videos para guardar")
        return
    
    # Crear directorio si no existe
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'videoId', 
            'videoTitle', 
            'channelTitle', 
            'publishedAt', 
            'duration',
            'categoryId',
            'viewCount', 
            'likeCount', 
            'commentCount',
            'commentsExtracted',
            'repliesExtracted',
            'totalInteractionsExtracted',
            'engagementRate',
            'videoUrl'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for stats in video_stats_list:
            writer.writerow(stats)
    
    print(f"\n{'='*60}")
    print(f"📊 Estadísticas generales guardadas en: {output_file}")
    print(f"Total de videos procesados: {len(video_stats_list)}")

def main():
    parser = argparse.ArgumentParser(description='Descarga comentarios de videos de YouTube')
    parser.add_argument('--api-key', required=True, help='Tu clave de API de YouTube Data v3')
    parser.add_argument('--max-results', type=int, default=1000, help='Número máximo de comentarios por video')
    parser.add_argument('--stats-file', default='estadisticas_videos.csv', help='Archivo CSV donde guardar estadísticas generales')
    
    args = parser.parse_args()
    
    # Inicializar el servicio de YouTube
    youtube = build('youtube', 'v3', developerKey=args.api_key)
    lista_urls = ['videosRenacer.txt', 'videosViceversa.txt', 'videosSabadosGloria.txt', 'videosAsuntosPendientes.txt']
    lista_output = ['comentarios/Renacer', 'comentarios/Viceversa', 'comentarios/SabadosGloria', 'comentarios/AsuntosPendientes']

    # Lista para almacenar estadísticas de todos los videos
    all_video_stats = []
    total_videos = 0

    for url_file, output_dir in zip(lista_urls, lista_output):
        # Leer las URLs del archivo
        try:
            with open(url_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print(f"⚠️ Archivo no encontrado: {url_file}, saltando...")
            continue
    
        for url in urls:
            video_id = extract_video_id(url)
            print(f"\n{'='*60}")
            print(f"Procesando video: {video_id}")
            
            # Obtener información del video
            video_info = get_video_info(youtube, video_id)
            print(f"Titulo: {video_info['title']}")
            print(f"Canal: {video_info['channelTitle']}")
            print(f"Visualizaciones: {video_info['viewCount']:,}")
            print(f"Likes: {video_info['likeCount']:,}")
            print(f"Comentarios totales: {video_info['commentCount']:,}")
            print(f"Duración: {video_info['duration']}")

            # Obtener comentarios
            comments = get_video_comments(youtube, video_id, video_info, args.max_results)
            
            # Contar comentarios extraídos y respuestas
            main_comments = sum(1 for c in comments if not c['isReply'])
            replies = sum(1 for c in comments if c['isReply'])
            
            # Calcular engagement rate (likes + comentarios) / visualizaciones * 100
            engagement_rate = 0
            if video_info['viewCount'] > 0:
                engagement_rate = ((video_info['likeCount'] + video_info['commentCount']) / video_info['viewCount']) * 100
            
            # Guardar estadísticas del video
            video_stats = {
                'videoId': video_id,
                'videoTitle': video_info['title'],
                'channelTitle': video_info['channelTitle'],
                'publishedAt': video_info['publishedAt'],
                'duration': video_info['duration'],
                'categoryId': video_info['categoryId'],
                'viewCount': video_info['viewCount'],
                'likeCount': video_info['likeCount'],
                'commentCount': video_info['commentCount'],
                'commentsExtracted': main_comments,
                'repliesExtracted': replies,
                'totalInteractionsExtracted': len(comments),
                'engagementRate': round(engagement_rate, 4),
                'videoUrl': f"https://www.youtube.com/watch?v={video_id}"
            }
            all_video_stats.append(video_stats)
            
            # Guardar comentarios
            save_comments_to_csv(video_id, comments, video_info['title'], output_dir)
            
            total_videos += 1
            
            # Pausa para evitar limites de cuota
            time.sleep(1)
    
    # Guardar estadísticas generales de todos los videos
    if all_video_stats:
        save_video_stats_to_csv(all_video_stats, args.stats_file)
        
    print(f"\n{'='*60}")
    print(f"✅ Proceso completado. Se procesaron {total_videos} videos en total.")

if __name__ == "__main__":
    main()
