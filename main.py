import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI()

os.makedirs("descargas", exist_ok=True)
app.mount("/descargas", StaticFiles(directory="descargas"), name="descargas")

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    # Si viene con /photo/, TikTok suele mapear el mismo ID bajo /video/ para yt-dlp
    url_limpia = url.split("?")[0]
    
    opciones = {
        'quiet': True,
        'outtmpl': 'descargas/%(id)s.mp4',
        'format': 'best[ext=mp4]/best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
    }

    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # Primero intentamos resolver si es una URL corta redirigida
            info = None
            try:
                info = ydl.extract_info(url, download=False)
            except Exception:
                # Si falló porque trae /photo/, probamos cambiando a /video/
                if "/photo/" in url:
                    url_video_alt = url.replace("/photo/", "/video/")
                    info = ydl.extract_info(url_video_alt, download=False)
                else:
                    raise

            if not info:
                raise Exception("No se pudo extraer información del enlace.")

            # Caso 1: Carrusel de fotos detectado por yt-dlp como entries o formatos de imagen
            if 'entries' in info and info['entries']:
                fotos_urls = []
                for entrada in info['entries']:
                    if 'url' in entrada:
                        fotos_urls.append(entrada['url'])
                    elif 'formats' in entrada and entrada['formats']:
                        fotos_urls.append(entrada['formats'][-1]['url'])

                return {
                    "estado": "exito",
                    "tipo": "fotos",
                    "titulo": info.get('title', 'Fotos_TikTok'),
                    "uploader": info.get('uploader', 'usuario_desconocido'),
                    "url_descarga": None,
                    "urls_fotos": fotos_urls
                }

            # Caso 2: Galería de imágenes dentro de un solo objeto info (algunos extractores usan 'thumbnails' o 'images')
            elif info.get('_type') == 'playlist' or 'entries' in info:
                # Si es lista vacía o formato no estándar
                raise Exception("Publicación de fotos sin streams directos legibles.")

            # Caso 3: Video normal
            else:
                info_descarga = ydl.extract_info(url, download=True)
                video_id = info_descarga.get('id')
                nombre_usuario = info_descarga.get('uploader', 'usuario_desconocido')

                url_base_segura = str(request.base_url).replace("http://", "https://")
                url_descarga_local = f"{url_base_segura}descargas/{video_id}.mp4"

                return {
                    "estado": "exito",
                    "tipo": "video",
                    "titulo": info_descarga.get('title', 'Video_TikTok'),
                    "uploader": nombre_usuario,
                    "url_descarga": url_descarga_local,
                    "urls_fotos": None
                }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
