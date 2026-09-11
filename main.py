import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI()

os.makedirs("descargas", exist_ok=True)
app.mount("/descargas", StaticFiles(directory="descargas"), name="descargas")

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    opciones = {
        'quiet': True,
        'outtmpl': 'descargas/%(id)s.mp4', 
        'format': 'best[ext=mp4]/best', 
        # Quitamos el noplaylist para que yt-dlp pueda leer el carrusel completo
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # 1. Inspeccionamos la URL SIN descargar nada todavía
            info = ydl.extract_info(url, download=False)
            
            # 2. Si tiene 'entries', significa que es un carrusel de fotos
            if 'entries' in info:
                # Extraemos solo las URLs directas de cada foto
                fotos_urls = [entrada['url'] for entrada in info['entries'] if 'url' in entrada]
                
                return {
                    "estado": "exito",
                    "tipo": "fotos", # ¡Nueva variable para avisarle a Android!
                    "titulo": info.get('title', 'Fotos_TikTok'),
                    "uploader": info.get('uploader', 'usuario_desconocido'),
                    "urls_fotos": fotos_urls # Mandamos la lista completa
                }
            
            # 3. Si no tiene 'entries', es un video normal. Lo descargamos en Render.
            else:
                info_descarga = ydl.extract_info(url, download=True)
                video_id = info_descarga.get('id')
                nombre_usuario = info_descarga.get('uploader', 'usuario_desconocido')
                
                url_base_segura = str(request.base_url).replace("http://", "https://")
                url_descarga_local = f"{url_base_segura}descargas/{video_id}.mp4"
                
                return {
                    "estado": "exito",
                    "tipo": "video", # Le avisamos a Android que es un video
                    "titulo": info_descarga.get('title', 'Video_TikTok'),
                    "uploader": nombre_usuario,
                    "url_descarga": url_descarga_local
                }
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
