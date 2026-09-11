import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI()

os.makedirs("descargas", exist_ok=True)
app.mount("/descargas", StaticFiles(directory="descargas"), name="descargas")

# Función para extraer el link real detrás de un enlace corto de compartir
def desenmascarar_url(url_corta: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # Hacemos una petición rápida para que TikTok nos redirija al enlace original
        res = requests.get(url_corta, headers=headers, allow_redirects=True, timeout=10)
        return res.url
    except:
        return url_corta

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    # 1. Desenmascaramos el link
    url_real = desenmascarar_url(url)
    
    # 2. AHORA SÍ revisamos si es foto y la engañamos cambiándola a video
    if "/photo/" in url_real:
        url_real = url_real.replace("/photo/", "/video/")
        
    # Limpiamos basura de tracking del link (?_r=1...)
    url_limpia = url_real.split("?")[0]
    
    opciones = {
        'quiet': True,
        'outtmpl': 'descargas/%(id)s.mp4',
        'format': 'best',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # Extraemos la información con la URL ya engañada
            info = ydl.extract_info(url_limpia, download=False)
            
            if not info:
                raise Exception("No se pudo extraer información.")

            # Caso 1: Carrusel de fotos (devuelve una lista de 'entries')
            if 'entries' in info and info['entries']:
                fotos_urls = []
                for entrada in info['entries']:
                    if 'url' in entrada:
                        fotos_urls.append(entrada['url'])
                
                return {
                    "estado": "exito",
                    "tipo": "fotos",
                    "titulo": info.get('title', 'Fotos_TikTok'),
                    "uploader": info.get('uploader', 'usuario_desconocido'),
                    "url_descarga": None,
                    "urls_fotos": fotos_urls
                }
            
            # Caso 2: Video normal o TikTok lo convirtió a MP4 automáticamente
            else:
                info_descarga = ydl.extract_info(url_limpia, download=True)
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
